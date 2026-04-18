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

| BOT | 类型 | 优先级 | 职责边界 |
|---|---|---|---|
| 逻辑BOT | 理性读者 | **最终审核** | 审查语言层级、角色一致性、格物逻辑、跨章连贯性 |
| 格物BOT | 理性读者 | 中 | 设计物理方案，确保解法有逻辑依据；方案必须服务叙事节奏 |
| 主架构BOT | 设计者 | 结构层 | 规划叙事骨架，不写正文 |
| 执笔BOT | 写手 | 执行层 | 将骨架和方案书变成正文；**执笔质量是关键**，爽感在写时解决，不靠后续审查补救 |

**核心原则：格物正确是底线，不是目标。**
格物BOT说"物理逻辑可信"，不代表章节好看。本作目标读者是休闲修仙读者——情节是否紧张、人物是否有感情、高潮是否落地，是执笔BOT的责任，不推给审查步骤。

---

## 每章流水线：四步 + 收尾

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
- 意见是规则性的 → 说「把这条规则加进bots/main-architect.md」

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
- bots/gewu.md
- drafts/0X_architect_brief.md

你的角色和指令在 bots/gewu.md 中。
任务：为第[X]章输出物理方案书。
```

**你的选择：**
- 满意 → 说「保存到 drafts/0X_physics_plan.md，进入第三步」
- 有意见 → 直接说，AI修改
- 意见是规则性的 → 说「把这条规则加进bots/gewu.md」

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
- 意见是规则性的 → 说「把这条规则加进bots/writer.md」

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
- 评级A/B → 把报告里的❌发回执笔人修改，修完进第五步
- 评级C/D → 把报告发回执笔人，说「根据审查报告重写以下段落」
- 逻辑员漏掉了某类问题 → 说「把这类检查加进bots/logic-reviewer.md」

循环执笔↔逻辑，直到评级达到A或B。

```bash
git add drafts/ && git commit -m "fix: 第X章根据审查修改"
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

## 作者反馈修改流程

> ⚠️ **仅适用于**：作者主动提出具体修改建议时（如"第X章反馈：……"类消息）。
> 自动化生成（第一至五步流水线）**不走此流程**，避免步骤重叠、前后冲突。

---

### 零、修改稿铁律（开始前先读，每次修改都适用）

> 反复出现的错误，往往来自对这一条的忽视。

**建议是目标，不是文本。**

任何建议——无论来自用户还是BOT审稿报告——都只描述了需要达到的效果。执笔人的任务是在读懂前后文之后，找到自然实现这个效果的方式，而不是把建议的原话插进去。

**零容忍行为（触发任意一项，修改不得提交）：**
- ❌ 建议的分析语言直接入文（"结论是……""好处是……""这是X的问题"）
- ❌ 正文出现章节数字（"第四章""上一章""本章"）——任何来源
- ❌ 建议原句被逐字搬进旁白/对白/内心活动
- ❌ 修改段落与前后文节奏/人物状态/场景走势断开，读者能感觉到"这里塞进来了什么"
- ❌ 只改了部分，同类问题在其他段落仍存在

---

### 一、拆解反馈

把每条建议转化为**具体的正文操作**，例如：
- "装置描述太细" → 第XX行起，压缩至N句
- "结果不明" → 在段落开头补一句，说明这件事做成了之后是什么状态
- "重复句式" → 找到具体位置，换写法

列出改动清单，逐条确认后再动笔。

---

### 二、执笔人修改

```
请读取：
- drafts/0X_draft.md
- bots/writer.md（重点读"修改稿行为准则"一节）
- MASTER_CODEX.md

作者反馈（已拆解为具体操作）：[列出改动清单]

任务：按清单修改对应段落，其余段落保持不动。修改后对每处改动确认：前后文衔接是否自然？
```

---

### 三、逻辑BOT复核（全章 + I项衔接检查）

```
请读取：
- MASTER_CODEX.md
- CHAPTER_LOG.md
- bots/logic-reviewer.md
- drafts/0X_draft.md（修改后版本）

任务：对修改后的全章执行七项审查，并额外执行 I项（修改段落衔接性检查）。
```

---

### 四、元语言扫描（提交前必过）

> 此步由Claude在commit前自行执行。逐项检查，任意一项触发则停止提交先修复。

- [ ] 正文中出现章节数字：「第X章」「上一章」「第X节」
- [ ] 正文中出现分析词汇直接入文：「结论是」「好处是」「这是X的问题」「从X角度」「X的代价」
- [ ] 反馈建议中的关键句被逐字搬进正文（逐句对比核查）
- [ ] 顾青台词或内心独白出现现代词汇（变量、系统、效率、参数等）
- [ ] 旁白中物理术语出现在括号外
- [ ] 修改段落与前后文走势、人物状态、场景节奏自然衔接——读者不会感觉到"这里插入了一段更新的内容"

---

### 五、提交

```bash
git add drafts/0X_draft.md
git commit -m "fix: 第X章作者反馈修订——[一句话概括改动]"
git push origin main
```

---



场景已清楚时，可以跳过第一步直接从第二步开始。

全自动触发：
```
读取所有相关文件，依次以格物BOT→执笔BOT→逻辑BOT的角色完成第X章，
逻辑BOT评级B以上则输出最终草稿，低于B则自动修改后再输出。
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
| 2026-04 | 全部 | 迁移至 bots/ 目录 |
| 2026-04 | writer | v2.6：新增"修改稿行为准则"节，零容忍项清单 |
| 2026-04 | logic-reviewer | 新增 I 项：修改段落衔接性检查 |
| 2026-04 | PIPELINE | 作者反馈修改流程加"零、铁律"、步骤重编 |
| 2026-04 | PIPELINE | 退役读者BOT步骤（arc-04执行评估：未能解决爽感问题，流水线改为四步） |

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
