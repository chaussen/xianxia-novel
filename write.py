#!/usr/bin/env python3
"""
《理法修途》写作工具

用法：
  python writer.py write 5            # 写第5章（读取已有章节1-4作为上下文）
  python writer.py write 5 9          # 顺序写第5到第9章
  python writer.py logic 5            # 逻辑审查第5章
  python writer.py logic 5 8          # 逻辑审查第5到8章（合并后整体审查）
  python writer.py consistency        # 一致性检查所有已有章节
  python writer.py consistency 9      # 一致性检查第1到9章
  python writer.py stitch             # 拼接所有章节到 preview/reading.md

通用选项：
  --model MODEL        DeepSeek 模型（默认 deepseek-chat，可用 deepseek-reasoner）
  --no-push            write 模式下提交但不推送
  --context N          write 模式下最多读入最近 N 章作为前文（默认 6，0 = 全部）
  --dry-run            仅打印将发送的 prompt，不调用 API

依赖：pip install openai
需要：DEEPSEEK_API_KEY 环境变量
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("错误：缺少 openai 库，请运行 pip install openai")
    sys.exit(1)


def _load_dotenv():
    """Load .env from the repo root if it exists (no extra dependencies)."""
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:   # env var takes precedence
            os.environ[key] = value

_load_dotenv()

# ── 目录常量 ─────────────────────────────────────────────────────────────────

REPO       = Path(__file__).parent
PUBLISHED  = REPO / "published"
CHAPTERS   = REPO / "chapters"      # AI 写作输出位置
PREVIEW    = REPO / "preview"
REVIEWS    = REPO / "reviews"

WRITE_PROMPT      = REPO / "DEEPSEEK_PROMPT.md"
LOGIC_PROMPT      = REPO / "LOGIC_PROMPT.md"
CONSISTENCY_PROMPT = REPO / "CONSISTENCY_PROMPT.md"

# 每次写作都注入的设定文件（顺序有意义：重要的先读）
SETTINGS_FILES = [
    (REPO / "MASTER_CODEX.md",          "世界观·人物·当前状态"),
    (REPO / "CHAPTER_LOG.md",           "章节日志·已用物理原理"),
    (REPO / "WORLD_CALENDAR.md",        "世界日历·背景事件"),
    (REPO / "TIANGONG_LILUE.md",        "天工理略残页管理"),
    (REPO / "WRITING_EXAMPLES.md",           "战斗场景例证"),
]


# ── 工具函数 ─────────────────────────────────────────────────────────────────

def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def run(cmd: list[str], check: bool = True) -> str:
    result = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"[!] 命令失败: {' '.join(cmd)}\n{result.stderr}")
        sys.exit(1)
    return result.stdout.strip()


def find_chapter(n: int) -> Path | None:
    """按优先级查找第 n 章文件：published/ > chapters/"""
    pub  = PUBLISHED / f"chapter-{n:02d}.md"
    chap = CHAPTERS  / f"chapter-{n:02d}.md"
    if pub.exists():  return pub
    if chap.exists(): return chap
    return None


def all_chapter_numbers() -> list[int]:
    """返回所有已存在章节的编号（升序）。"""
    nums = set()
    for d in (PUBLISHED, CHAPTERS):
        for f in d.glob("chapter-??.md"):
            try:
                nums.add(int(f.stem.split("-")[1]))
            except (ValueError, IndexError):
                pass
    return sorted(nums)


def section(label: str, content: str) -> str:
    bar = "=" * 60
    return f"{bar}\n【{label}】\n{bar}\n{content}"


def call_api(client: OpenAI, model: str, system: str,
             messages: list[dict], max_tokens: int = 6000,
             dry_run: bool = False) -> str:
    """调用 DeepSeek API，流式输出，返回完整文本。"""
    if dry_run:
        total_chars = sum(len(m["content"]) for m in messages) + len(system)
        print(f"\n[dry-run] 系统提示词: {len(system)} 字符")
        print(f"[dry-run] 上下文总计: {total_chars} 字符 (~{total_chars // 3} tokens 估算)")
        print(f"[dry-run] 模型: {model}\n")
        print("--- 用户消息 (最后一条) ---")
        print(messages[-1]["content"][:600])
        print("--- end ---")
        return ""

    full = ""
    with client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}] + messages,
        stream=True,
        max_tokens=max_tokens,
        temperature=1.0,
    ) as stream:
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                print(delta, end="", flush=True)
                full += delta
    print()
    return full


# ── write 模式 ───────────────────────────────────────────────────────────────

def build_write_context(chapter_num: int, context_n: int) -> str:
    """构建写作上下文：设定文件 + 前 N 章正文。"""
    parts = []

    # 设定文件
    for path, label in SETTINGS_FILES:
        content = read(path)
        if content:
            parts.append(section(label, content))

    # 前 N 章（从最近往前，不超过 context_n 章）
    prev_nums = [n for n in all_chapter_numbers() if n < chapter_num]
    if context_n > 0:
        prev_nums = prev_nums[-context_n:]   # 只取最近的 N 章

    for n in prev_nums:
        path = find_chapter(n)
        if path:
            parts.append(section(f"第{n}章（{'已发布' if path.parent == PUBLISHED else '已写'}）",
                                 read(path)))

    return "\n\n".join(parts)


def write_chapter(client: OpenAI, chapter_num: int,
                  model: str, context_n: int,
                  no_push: bool, dry_run: bool):
    out_path = CHAPTERS / f"chapter-{chapter_num:02d}.md"

    if out_path.exists() and not dry_run:
        print(f"[!] 已存在：{out_path.name}")
        if input("    覆盖？(y/N): ").strip().lower() != "y":
            print("已跳过。")
            return

    system = read(WRITE_PROMPT)
    if not system:
        print(f"错误：找不到 {WRITE_PROMPT}")
        sys.exit(1)

    print(f"\n[~] 构建第{chapter_num}章上下文…")
    context = build_write_context(chapter_num, context_n)

    user_msg = (
        f"请写**第{chapter_num}章**的完整正文。\n\n"
        f"要求：\n"
        f"- 直接从 `# 第{chapter_num}章：[章节标题]` 开始输出\n"
        f"- 自然接续上一章的叙事状态和人物位置\n"
        f"- 三层语言：对白/独白用土著语言，旁白不出现物理术语，物理律名只在括号里\n"
        f"- 格物原理来自《天工理略》原文或现场观察，不凭空灵光一闪\n"
        f"- 章末附上〔账本余页〕（当日损耗/收益/净核算）\n"
        f"- 约2000—3500字"
    )

    print(f"[~] 正在写第{chapter_num}章（模型：{model}）…")
    print("-" * 60)

    text = call_api(client, model,
                    system=system,
                    messages=[{"role": "user", "content": context},
                               {"role": "user", "content": user_msg}],
                    dry_run=dry_run)

    if dry_run or not text.strip():
        return

    print("-" * 60)
    CHAPTERS.mkdir(exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    print(f"[✓] 已保存：{out_path}")

    # 提交
    run(["git", "add", str(out_path)])
    run(["git", "commit", "-m", f"draft: 第{chapter_num}章（DeepSeek）"])
    print(f"[✓] 已提交第{chapter_num}章")

    if not no_push:
        run(["git", "push", "origin", "main"])
        print("[✓] 已推送")


# ── logic 模式 ───────────────────────────────────────────────────────────────

def run_logic(client: OpenAI, start: int, end: int,
              model: str, dry_run: bool):
    system = read(LOGIC_PROMPT)
    if not system:
        print(f"错误：找不到 {LOGIC_PROMPT}")
        sys.exit(1)

    # 设定文件（MASTER_CODEX + CHAPTER_LOG 即可）
    codex = read(REPO / "MASTER_CODEX.md")
    log   = read(REPO / "CHAPTER_LOG.md")
    parts = [section("世界观·人物·禁止事项", codex),
             section("章节日志", log)]

    # 待审查章节
    for n in range(start, end + 1):
        path = find_chapter(n)
        if path:
            parts.append(section(f"第{n}章正文", read(path)))
        else:
            print(f"[!] 找不到第{n}章，跳过")

    context = "\n\n".join(parts)
    range_str = f"{start}" if start == end else f"{start}-{end}"
    user_msg = f"请对上方第{range_str}章的内容执行完整的七项逻辑审查，输出审查报告。"

    print(f"\n[~] 逻辑审查第{range_str}章（模型：{model}）…")
    print("-" * 60)

    report = call_api(client, model,
                      system=system,
                      messages=[{"role": "user", "content": context},
                                 {"role": "user", "content": user_msg}],
                      max_tokens=4000,
                      dry_run=dry_run)

    if dry_run or not report.strip():
        return

    print("-" * 60)
    REVIEWS.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%m%d-%H%M")
    out_path = REVIEWS / f"logic-ch{range_str}-{ts}.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"[✓] 审查报告已保存：{out_path}")


# ── consistency 模式 ─────────────────────────────────────────────────────────

def run_consistency(client: OpenAI, up_to: int | None,
                    model: str, dry_run: bool):
    system = read(CONSISTENCY_PROMPT)
    if not system:
        print(f"错误：找不到 {CONSISTENCY_PROMPT}")
        sys.exit(1)

    nums = all_chapter_numbers()
    if up_to is not None:
        nums = [n for n in nums if n <= up_to]

    if not nums:
        print("[!] 没有找到任何章节")
        return

    codex = read(REPO / "MASTER_CODEX.md")
    log   = read(REPO / "CHAPTER_LOG.md")
    cal   = read(REPO / "WORLD_CALENDAR.md")
    parts = [section("世界观·人物·禁止事项", codex),
             section("章节日志", log),
             section("世界日历", cal)]

    for n in nums:
        path = find_chapter(n)
        if path:
            parts.append(section(f"第{n}章正文", read(path)))

    context = "\n\n".join(parts)
    range_str = f"1-{nums[-1]}"
    user_msg = (
        f"请对第{range_str}章（共{len(nums)}章）做全局一致性检查，"
        f"输出完整报告，包括道具追踪、人物一致性、物理原理复用、"
        f"悬念遗漏、铺垫落地比例等五类分析。"
    )

    print(f"\n[~] 一致性检查第{range_str}章（共{len(nums)}章，模型：{model}）…")
    print("-" * 60)

    report = call_api(client, model,
                      system=system,
                      messages=[{"role": "user", "content": context},
                                 {"role": "user", "content": user_msg}],
                      max_tokens=6000,
                      dry_run=dry_run)

    if dry_run or not report.strip():
        return

    print("-" * 60)
    REVIEWS.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%m%d-%H%M")
    out_path = REVIEWS / f"consistency-{range_str}-{ts}.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"[✓] 一致性报告已保存：{out_path}")


# ── stitch 模式 ──────────────────────────────────────────────────────────────

def run_stitch():
    """拼接所有章节（published/ + chapters/）到 preview/reading.md。"""
    PREVIEW.mkdir(exist_ok=True)
    parts = []

    # 序章
    prologue = PUBLISHED / "prologue.md"
    if prologue.exists():
        parts.append(read(prologue))

    # 所有章节（升序）
    nums = all_chapter_numbers()
    for n in nums:
        path = find_chapter(n)
        if path:
            parts.append(read(path))

    if not parts:
        print("[!] 没有找到任何章节")
        return

    header = (
        "# 《理法修途》— 本地阅读合并版\n\n"
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}"
        f"　|　章节数：{len(nums)}\n"
    )
    out = header + "\n\n---\n\n".join(parts)

    out_path = PREVIEW / "reading.md"
    out_path.write_text(out, encoding="utf-8")
    print(f"[✓] 已生成：{out_path}（{len(nums)}章 + {'序章' if prologue.exists() else '无序章'}）")


# ── CLI ──────────────────────────────────────────────────────────────────────

def get_client(dry_run: bool) -> OpenAI | None:
    if dry_run:
        return None
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("错误：请设置 DEEPSEEK_API_KEY 环境变量")
        sys.exit(1)
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


def main():
    p = argparse.ArgumentParser(description="《理法修途》写作工具")
    sub = p.add_subparsers(dest="cmd", required=True)

    # write
    pw = sub.add_parser("write", help="写章节")
    pw.add_argument("start", type=int, help="起始章节编号")
    pw.add_argument("end",   type=int, nargs="?", help="结束章节编号（省略则只写一章）")
    pw.add_argument("--context", type=int, default=6,
                    help="最多读入最近 N 章作为前文（0=全部，默认6）")
    pw.add_argument("--no-push", action="store_true")
    pw.add_argument("--model",   default="deepseek-chat")
    pw.add_argument("--dry-run", action="store_true")

    # logic
    pl = sub.add_parser("logic", help="逻辑审查")
    pl.add_argument("start", type=int, help="审查起始章节")
    pl.add_argument("end",   type=int, nargs="?", help="审查结束章节（省略=只审一章）")
    pl.add_argument("--model",   default="deepseek-chat")
    pl.add_argument("--dry-run", action="store_true")

    # consistency
    pc = sub.add_parser("consistency", help="全局一致性检查")
    pc.add_argument("up_to", type=int, nargs="?",
                    help="检查到第几章（省略=全部已有章节）")
    pc.add_argument("--model",   default="deepseek-chat")
    pc.add_argument("--dry-run", action="store_true")

    # stitch
    sub.add_parser("stitch", help="拼接所有章节到 preview/reading.md")

    args = p.parse_args()

    if args.cmd == "stitch":
        run_stitch()
        return

    dry = getattr(args, "dry_run", False)
    model = getattr(args, "model", "deepseek-chat")
    client = get_client(dry)
    if dry:
        # 创建一个假 client 占位（dry-run 不实际调用）
        client = object()

    if args.cmd == "write":
        end = args.end if args.end else args.start
        for n in range(args.start, end + 1):
            write_chapter(client, n,
                          model=model,
                          context_n=args.context,
                          no_push=args.no_push,
                          dry_run=dry)

    elif args.cmd == "logic":
        end = args.end if args.end else args.start
        run_logic(client, args.start, end, model=model, dry_run=dry)

    elif args.cmd == "consistency":
        run_consistency(client, args.up_to, model=model, dry_run=dry)


if __name__ == "__main__":
    main()
