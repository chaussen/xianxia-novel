#!/usr/bin/env python3
"""
《理法修途》DeepSeek 写作客户端
用法：
  python writer.py 05                    # 写第5章，自动检测 arc 骨架
  python writer.py 05 --arc 05           # 指定使用 arc05 骨架
  python writer.py 05 --no-push          # 写完提交但不推送
  python writer.py 05 --model deepseek-reasoner  # 使用 R1 模型
  python writer.py 05 --dry-run          # 只构建 prompt，打印后退出

依赖：pip install openai
需要：DEEPSEEK_API_KEY 环境变量
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("错误：缺少 openai 库，请运行 pip install openai")
    sys.exit(1)

REPO = Path(__file__).parent
DRAFTS = REPO / "drafts"
PUBLISHED = REPO / "published"
SYSTEM_PROMPT_FILE = REPO / "DEEPSEEK_PROMPT.md"

CONTEXT_FILES = [
    ("MASTER_CODEX.md",             "世界观·人物·当前状态"),
    ("CHAPTER_LOG.md",              "章节日志·已用物理原理"),
    ("WORLD_CALENDAR.md",           "世界日历·背景事件"),
    ("TIANGONG_LILUE.md",           "天工理略残页管理"),
    ("bots/WRITING_EXAMPLES.md",    "战斗场景例证"),
]


# ── helpers ──────────────────────────────────────────────────────────────────

def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def run(cmd: list[str], **kwargs):
    result = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, **kwargs)
    if result.returncode != 0:
        print(f"[!] 命令失败: {' '.join(cmd)}")
        print(result.stderr)
        sys.exit(1)
    return result.stdout.strip()


def detect_arc(chapter_num: int) -> int | None:
    """从 arc architect brief 文件名推断当前 arc 编号。

    策略：
    - 如果当前章节已有草稿，不强制加载 arc 骨架（草稿本身提供了连续性）
    - 如果没有草稿（新章节），使用最新的 arc brief
    """
    current_draft = DRAFTS / f"{chapter_num:02d}_draft.md"
    if current_draft.exists():
        return None  # 已有草稿，arc 骨架不关键

    candidates = sorted(DRAFTS.glob("arc??_architect_brief.md"), reverse=True)
    if candidates:
        return int(candidates[0].name[3:5])
    return None


def build_context(chapter_num: int, arc_num: int | None) -> str:
    """拼装所有上下文文件为单个字符串。"""
    parts = []

    # 核心参考文件
    for filename, label in CONTEXT_FILES:
        content = read(REPO / filename)
        if content:
            parts.append(f"{'='*60}\n【{label}】{filename}\n{'='*60}\n{content}")

    # Arc 骨架
    if arc_num is not None:
        brief_path = DRAFTS / f"arc{arc_num:02d}_architect_brief.md"
        brief = read(brief_path)
        if brief:
            parts.append(
                f"{'='*60}\n【当前弧线骨架】arc{arc_num:02d}_architect_brief.md\n{'='*60}\n{brief}"
            )
        else:
            print(f"[!] 找不到 {brief_path.name}，跳过弧线骨架")

    # 上一章（优先已发布版，其次草稿）
    prev = chapter_num - 1
    prev_published = PUBLISHED / f"chapter-{prev:02d}.md"
    prev_draft = DRAFTS / f"{prev:02d}_draft.md"

    if prev_published.exists():
        parts.append(
            f"{'='*60}\n【上一章（已发布）】chapter-{prev:02d}.md\n{'='*60}\n{read(prev_published)}"
        )
    elif prev_draft.exists():
        parts.append(
            f"{'='*60}\n【上一章（草稿）】{prev:02d}_draft.md\n{'='*60}\n{read(prev_draft)}"
        )
    else:
        print(f"[!] 找不到第{prev}章内容，无前章参考")

    return "\n\n".join(parts)


def build_user_message(chapter_num: int) -> str:
    return f"""请根据上方所有参考材料，写**第{chapter_num}章**的完整正文。

要求：
- 直接从 `# 第{chapter_num}章：[章节标题]` 开始输出
- 自然接续上一章的叙事状态和人物位置
- 三层语言：对白/独白用土著语言，旁白不出现物理术语，物理律名只在括号里
- 格物原理来自《天工理略》原文或现场观察，不凭空灵光一闪
- 章末附上〔账本余页〕（当日损耗/收益/净核算）
- 约2000—3500字"""


# ── git ──────────────────────────────────────────────────────────────────────

def git_commit_push(chapter_num: int, no_push: bool):
    draft_path = DRAFTS / f"{chapter_num:02d}_draft.md"
    run(["git", "add", str(draft_path)])

    commit_msg = f"draft: 第{chapter_num}章草稿（DeepSeek 自动写作）"
    run(["git", "commit", "-m", commit_msg])
    print(f"[✓] 已提交：{commit_msg}")

    if not no_push:
        run(["git", "push", "origin", "main"])
        print("[✓] 已推送到 GitHub")
    else:
        print("[~] 跳过推送（--no-push）")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="《理法修途》DeepSeek 写作客户端")
    parser.add_argument("chapter", type=int, help="要写的章节编号（如 5）")
    parser.add_argument("--arc", type=int, default=None, help="手动指定 arc 编号（如 05）")
    parser.add_argument("--no-push", action="store_true", help="提交但不推送到 GitHub")
    parser.add_argument("--model", default="deepseek-chat",
                        help="DeepSeek 模型（deepseek-chat / deepseek-reasoner）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只构建并打印 prompt，不调用 API")
    parser.add_argument("--max-tokens", type=int, default=4096, help="最大输出 token 数")
    args = parser.parse_args()

    chapter_num = args.chapter

    # 检查 API Key
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key and not args.dry_run:
        print("错误：请设置 DEEPSEEK_API_KEY 环境变量")
        sys.exit(1)

    # 检查系统提示词
    system_prompt = read(SYSTEM_PROMPT_FILE)
    if not system_prompt:
        print(f"错误：找不到 {SYSTEM_PROMPT_FILE}")
        sys.exit(1)

    # 检查草稿是否已存在
    draft_path = DRAFTS / f"{chapter_num:02d}_draft.md"
    if draft_path.exists() and not args.dry_run:
        print(f"[!] 草稿已存在：{draft_path.name}")
        answer = input("    覆盖？(y/N): ").strip().lower()
        if answer != "y":
            print("已取消。")
            sys.exit(0)

    # 自动检测 arc
    arc_num = args.arc
    if arc_num is None:
        arc_num = detect_arc(chapter_num)
        if arc_num:
            print(f"[~] 自动检测到 arc{arc_num:02d} 骨架")

    # 构建上下文
    print(f"[~] 构建第{chapter_num}章上下文...")
    context = build_context(chapter_num, arc_num)
    user_msg = build_user_message(chapter_num)

    if args.dry_run:
        print("\n" + "="*60)
        print("【系统提示词 (首300字符)】")
        print(system_prompt[:300] + "...")
        print("="*60)
        print(f"【上下文长度】{len(context)} 字符 (~{len(context)//3} tokens 估算)")
        print("【用户消息】")
        print(user_msg)
        print("="*60)
        print("[dry-run] 已完成，未调用 API")
        return

    # 调用 DeepSeek
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    print(f"[~] 正在生成第{chapter_num}章（模型：{args.model}）...")
    print("-" * 60)

    full_text = ""
    try:
        with client.chat.completions.create(
            model=args.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context},
                {"role": "user", "content": user_msg},
            ],
            stream=True,
            max_tokens=args.max_tokens,
            temperature=1.0,
        ) as stream:
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    print(delta, end="", flush=True)
                    full_text += delta
    except KeyboardInterrupt:
        print("\n\n[!] 已中断")
        if full_text and input("保存已生成内容？(y/N): ").strip().lower() == "y":
            pass  # 继续保存
        else:
            sys.exit(0)

    print("\n" + "-" * 60)

    if not full_text.strip():
        print("[!] API 返回内容为空，已跳过保存")
        sys.exit(1)

    # 保存草稿
    DRAFTS.mkdir(exist_ok=True)
    draft_path.write_text(full_text, encoding="utf-8")
    print(f"[✓] 已保存：{draft_path}")

    # 提交推送
    try:
        git_commit_push(chapter_num, args.no_push)
    except SystemExit:
        print("[!] git 操作失败，草稿文件已保存，请手动提交")


if __name__ == "__main__":
    main()
