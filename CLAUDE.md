# Claude Code 项目规则 — 理法修途

## 分支策略：单一开发分支

所有工作在 `claude/review-latest-changes-98lco` 上进行。Claude 不与 `main` 分支交互。

- 每章草稿、维护文件更新、修订均直接提交到 `claude/review-latest-changes-98lco`
- 写完直接 `git push origin claude/review-latest-changes-98lco`
- **禁止**执行 `git pull`、`git fetch`、`git checkout main` 或任何涉及 `main` 的操作
- 用户在 GitHub 上按需发起 PR 将此分支合并到 `main`；Claude 无需感知 PR 状态

### 文件目录约定
| 目录 | 用途 | 操作时机 |
|---|---|---|
| `chapters/` | AI 写作输出（草稿） | `write.py write N` 自动保存 |
| `published/` | 正式发布 | 用户确认"发布"后归档 |

### preview/combined.md
- `preview/combined.md` 由 GitHub Actions **自动生成**，合并 `published/` + `chapters/` 供预览
- **禁止手动生成或提交**，不要在 `git add` 中包含此文件

---

## 工作流一：CLI 脚本（write.py + DeepSeek API）

使用 `write.py` 进行所有写作和审查工作：

```bash
python write.py write 5          # 写第5章
python write.py write 5 9        # 顺序写第5到第9章
python write.py logic 5 8        # 逻辑审查第5到8章
python write.py consistency      # 全局一致性检查
python write.py stitch           # 拼接到 preview/reading.md
```

需要 `DEEPSEEK_API_KEY`（在 `.env` 或环境变量中设置）。

**定稿前必须停下来让用户审阅**，不在用户确认前执行：
- 文件归档（`chapters/` → `published/`）
- 更新 `CHAPTER_LOG.md` / `WORLD_CALENDAR.md` / `MASTER_CODEX.md`

---

## 工作流二：直接会话写作（Claude Code）

在此对话中直接写作时，遵守以下流程：

### 写作前（必读）
每次写新章前，按顺序读取：
1. `MASTER_CODEX.md` — 世界观、人物、当前状态、禁止事项
2. `CHAPTER_LOG.md` — 已用物理原理、章节进度
3. `WORLD_CALENDAR.md` — 当前背景事件
4. `TIANGONG_LILUE.md` — 残页管理，确认可用残页编号
5. 最近 2—4 章正文（`published/` 或 `chapters/`）

### 输出
- 章节正文直接输出到对话，供用户审阅
- 用户确认后，写入 `chapters/chapter-NN.md`，提交到 `main`
- 提交信息格式：`draft: 第N章`

### 篇幅与节奏（每章必须遵守）
- **目标篇幅：约三千中文字符**（含账本余页）
- **技术与描写的平衡**：物理洞察必须被具体感官细节稀释——场所的气味与温度、人物的姿势与细节、道具的质感与状态、等待的身体感受。连续两段以上的机理推导即为失衡。格物原理通过观察到的现象和可见的证据呈现，不直接陈述为机理链条。目标读者是普通读者，不是物理爱好者。

### 审查
- 逻辑审查和一致性检查：直接在对话中输出报告，不写文件
- 若用户需要保存报告，询问后写入 `reviews/`

### 设定更新
- 用户批准后才更新 `CHAPTER_LOG.md` / `WORLD_CALENDAR.md` / `MASTER_CODEX.md`
- 更新时精确修改对应字段，不重写整个文件

---

## 创作核心约束（每次写作必须遵守）

1. **MASTER_CODEX 优先**：所有创作决策以 `MASTER_CODEX.md` 为最终权威
2. **顾青不是工程师**：他比旁人多想一步、观察更仔细，但绝不设计系统性实验或控制变量
3. **知识来源可追溯**：顾青使用任何物理原理，必须来自《天工理略》原文或现场直接观察
4. **语言三层架构**：对白/独白无现代词；旁白无物理术语；物理律名仅在括号注里出现
5. **禁用现代词汇**：对白与独白中禁止"变量、样本、参数、效率、系统、数据"等词
6. **《天工理略》管理**：写新章前必须查阅 `TIANGONG_LILUE.md`，确认残页编号、登记使用、遵守文体规范。作者专用内容绝对不入叙事。
