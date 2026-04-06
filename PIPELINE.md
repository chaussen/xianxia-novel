# 流水线操作手册 PIPELINE

> 适用于：Claude Code CLI / Gemini CLI / 任何主流AI命令行工具
> 所有prompt可直接复制粘贴，替换[方括号]内容即可

---

## 仓库结构速查

```
xianxia-novel/
├── MASTER_CODEX.md          ← 世界观、人物、禁止事项（所有BOT必读）
├── CHAPTER_LOG.md           ← 章节日志、已用物理原理
├── WORLD_CALENDAR.md        ← 弃剑坑背景事件
├── CHAPTER_CHECKLIST.md     ← 章节收尾检查表
├── PIPELINE.md              ← 本文件
├── TIANGONG_LILUE.md        ← 《天工理略》残页管理
├── drafts/                  ← 草稿区（定稿未发布也留在此处）
├── published/               ← 已发布章节归档
└── bots/
    ├── main-architect.md    ← 主架构BOT
    ├── gewu.md              ← 格物BOT（理性）
    ├── writer.md            ← 执笔BOT
    ├── logic-reviewer.md    ← 逻辑BOT
    └── reader.md            ← 读者BOT（感性，最高优先级）
```

---

## BOT层级说明

本流水线有两类BOT，地位不同：

| BOT | 类型 | 优先级 | 职责边界 |
|---|---|---|---|
| 读者BOT | 感性读者 | **最高** | 判断章节是否吸引人、节奏是否顺、爽点是否落地 |
| 逻辑BOT | 理性读者 | 高 | 审查语言层级、角色一致性、格物逻辑、跨章连贯性 |
| 格物BOT | 理性读者 | 中 | 设计物理方案，确保解法有逻辑依据 |
| 主架构BOT | 设计者 | 结构层 | 规划叙事骨架，不写正文 |
| 执笔BOT | 写手 | 执行层 | 将骨架和方案书变成正文 |

**核心原则：读者BOT的意见高于格物BOT。**
格物BOT说"物理逻辑可信"，但读者BOT说"这段我跳过了"，那这段就有问题——答案不是加更多解释，而是削减物理细节。本作目标读者是休闲修仙读者，不是物理爱好者。

---

## 每章流水线：五步 + 收尾

### 准备：分支判断

**情况A：新叙事单元，无对应 arc 分支**
```bash
git checkout -b arc-NN
git push -u origin arc-NN
```
单元边界（包含哪几章、叙事冲突是什么）写进第一个 commit message。

**情况B：已在正确 arc 分支上**
同一叙事单元内的新章节 → 在同一分支追加提交，不新建：
```bash
git branch --show-current
```

> ⚠️ 任何分支合并进 main 都必须通过 PR，不直接 merge。

---

### 第一步：主架构BOT（场景规划）

**输入以下prompt：**
```
请读取以下文件内容：
- MASTER_CODEX.md
- CHAPTER_LOG.md
- WORLD_CALENDAR.md
- bots/main-architect.md

你的角色和指令在 bots/main-architect.md 中。
任务：为第[X]章规划场景骨架，并说明需要更新的世界日历内容。
```

**你的选择：**
- 满意 → 说「保存到 drafts/0X_architect_brief.md，进入第二步」
- 有意见 → 直接说意见，AI修改后重新确认
- 意见是规则性的 → 说「把这条规则加进 bots/main-architect.md」

```bash
git add drafts/ bots/ && git commit -m "chore: 第X章场景规划"
```

---

### 第二步：格物BOT（物理方案书）

> 格物BOT是**理性读者**，负责让物理解法可信。它的方案必须服务于故事节奏，不是反过来。
> 如果完整的物理解释会拖慢叙事，格物BOT应主动标注哪些细节可以省略。

**输入以下prompt：**
```
请读取以下文件内容：
- MASTER_CODEX.md
- CHAPTER_LOG.md
- WORLD_CALENDAR.md
- TIANGONG_LILUE.md
- bots/gewu.md
- drafts/0X_architect_brief.md

你的角色和指令在 bots/gewu.md 中。
任务：为第[X]章输出物理方案书。
```

**你的选择：**
- 满意 → 说「保存到 drafts/0X_physics_plan.md，进入第三步」
- 有意见 → 直接说，AI修改
- 意见是规则性的 → 说「把这条规则加进 bots/gewu.md」

```bash
git add drafts/ bots/ && git commit -m "chore: 第X章物理方案书"
```

---

### 第三步：执笔BOT（正文草稿）

**输入以下prompt：**
```
请读取以下文件内容：
- MASTER_CODEX.md
- bots/writer.md
- drafts/0X_physics_plan.md

你的角色和指令在 bots/writer.md 中。
任务：根据物理方案书，写第[X]章正文草稿。
章节末尾附上更新后的状态监测。
```

**你的选择：**
- 满意 → 说「保存到 drafts/0X_draft.md，进入第四步」
- 有意见 → 直接说，AI修改
- 意见是规则性的 → 说「把这条规则加进 bots/writer.md」

```bash
git add drafts/ bots/ && git commit -m "draft: 第X章初稿"
```

---

### 第四步：逻辑BOT（审查）

**输入以下prompt：**
```
请读取以下文件内容：
- MASTER_CODEX.md
- CHAPTER_LOG.md
- bots/logic-reviewer.md
- drafts/0X_draft.md

你的角色和指令在 bots/logic-reviewer.md 中。
任务：对第[X]章草稿进行七项审查，输出审查报告。
```

**你的选择：**
- 评级A/B → 把报告里的❌发回执笔BOT修改，修完进第五步
- 评级C/D → 把报告发回执笔BOT，说「根据审查报告重写以下段落」
- 逻辑BOT漏掉了某类问题 → 说「把这类检查加进 bots/logic-reviewer.md」

循环执笔↔逻辑，直到评级达到A或B。

```bash
git add drafts/ && git commit -m "fix: 第X章根据审查修改"
```

---

### 第五步：读者BOT（体验反馈）

> 读者BOT是**感性读者**，优先级最高。它不检查物理是否正确，只看章节是否吸引人。
> 读者BOT说"跳过"的段落，不应该用更多物理解释来修，而应该削减或重组。

**输入以下prompt：**
```
请读取以下文件内容：
- bots/reader.md
- drafts/0X_draft.md

你的角色和指令在 bots/reader.md 中。
任务：以读者身份对第[X]章草稿给出五项体验反馈。
```

**你的选择：**
- 综合评价"会点开下一章" → 可以定稿
- 有明确的跳读区/爽点未落地 → 把读者报告发回执笔BOT，说「根据读者反馈修改以下段落」
- 反馈是规则性的 → 说「把这条加进 bots/reader.md」

> 读者BOT只报告问题，不给修改方案。执笔BOT负责想怎么改。
> 不要求"一定会点开下一章"——"也许会"就够，不需要100%满意。

```bash
git add drafts/ && git commit -m "fix: 第X章读者反馈修改"
```

---

### 收尾：定稿提交

先按 `CHAPTER_CHECKLIST.md` 逐项核对，补完所有未完成项，再提交。

```bash
git add .
git commit -m "release: 第X章定稿，更新世界日历和章节日志"
git push origin arc-NN
```

> ⚠️ 不直接 merge 进 main。定稿后开 PR，由用户审批合并。

---

### 发布归档：用户说"已发布"时执行

1. 将定稿正文复制到 `published/` 目录：
   - 序章：`published/prologue.md`
   - 第X章：`published/chapter-[0X].md`

2. 文件格式：
   ```markdown
   # 第X章：[章节标题]
   
   > 作者：冏｜来源：LOFTER
   
   ---
   
   【章末状态】
   修为境界：…
   核心道具：…
   
   ---
   
   [正文]
   ```

3. 提交：
   ```bash
   git add published/
   git commit -m "published: 第X章已发布，归档至published/"
   git push origin arc-NN
   ```

---

## 跳步操作（熟悉后）

场景已清楚时，可以跳过第一步直接从第二步开始。

全自动触发：
```
读取所有相关文件，依次以格物BOT→执笔BOT→逻辑BOT的角色完成第X章，
逻辑BOT评级B以上则输出最终草稿，低于B则自动修改后再输出。
完成后等待读者BOT反馈，再决定是否定稿。
```

---

## BOT进化记录

每次修改 bots/ 下的文件后，在此处简单记录：

| 日期 | BOT | 修改内容 |
|---|---|---|
| 2026-03 | writer | v2.1-2.2：意象/语言纯净度规则 |
| 2026-03 | logic-reviewer | 新增：配角合理性检查 |
| 2026-03 | main-architect/writer/logic-reviewer | v2.4：背景-前景距离原则 |
| 2026-03 | reader | v1.0：新增读者BOT，五步流水线 |
| 2026-04 | writer | v2.5：三级账本制、节奏/对比原则 |
| 2026-04 | logic-reviewer | B项同步三级账本制，删除旧"情绪单位化"规则 |
| 2026-04 | 全部 | 迁移至 bots/ 目录；读者BOT优先级说明 |

---

## 常见问题

**Q：AI读不到文件怎么办？**
直接把文件内容复制粘贴进prompt。

**Q：某步输出格式不对怎么办？**
说「按照 bots/[对应BOT].md 要求的格式重新输出」，同时检查BOT文件的格式要求是否清晰。

**Q：两个AI（Claude/Gemini）输出风格不一致怎么办？**
执笔BOT步骤固定用一个AI，其他步骤可以混用。执笔风格一致性最重要。

**Q：读者BOT和格物BOT意见冲突怎么办？**
读者BOT优先。削减物理解释，不是增加。
