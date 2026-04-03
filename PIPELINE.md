# 流水线操作手册 PIPELINE

> 适用于：Claude Code CLI / Gemini CLI / 任何主流AI命令行工具
> 所有prompt可直接复制粘贴，替换[方括号]内容即可

---

## 仓库结构速查

```
xianxia-novel/
├── MASTER_CODEX.md        ← 世界观、人物、禁止事项（所有BOT必读）
├── CHAPTER_LOG.md         ← 章节日志、已用物理原理
├── WORLD_CALENDAR.md      ← 弃剑坑背景事件
├── CHAPTER_CHECKLIST.md   ← 章节收尾检查表
├── PIPELINE.md            ← 本文件
├── chapters/              ← 已定稿章节
├── drafts/                ← 草稿区
└── bots/
    ├── main-architect/PROMPT.md
    ├── gewu-agent/PROMPT.md
    ├── writer-agent/PROMPT.md
    └── logic-reviewer/PROMPT.md
```

---

## 每章流水线：四步 + 收尾

### 准备：新建分支
```bash
git checkout -b chapter-[章节号]
```

---

### 第一步：主架构师（场景规划）

**输入以下prompt：**
```
请读取以下文件内容：
- MASTER_CODEX.md
- CHAPTER_LOG.md
- WORLD_CALENDAR.md
- bots/main-architect/PROMPT.md

你的角色和指令在PROMPT.md中。
任务：为第[X]章规划场景骨架，并说明需要更新的世界日历内容。
```

**你的选择：**
- 满意 → 说「保存到drafts/0X_architect_brief.md，进入第二步」
- 有意见 → 直接说意见，AI修改后重新确认
- 意见是规则性的 → 说「把这条规则加进bots/main-architect/PROMPT.md」

```bash
git add drafts/ bots/ && git commit -m "chore: 第X章场景规划"
```

---

### 第二步：格物院（物理方案书）

**输入以下prompt：**
```
请读取以下文件内容：
- MASTER_CODEX.md
- CHAPTER_LOG.md
- WORLD_CALENDAR.md
- bots/gewu-agent/PROMPT.md
- drafts/0X_architect_brief.md

你的角色和指令在PROMPT.md中。
任务：为第[X]章输出物理方案书。
```

**你的选择：**
- 满意 → 说「保存到drafts/0X_physics_plan.md，进入第三步」
- 有意见 → 直接说，AI修改
- 意见是规则性的 → 说「把这条规则加进bots/gewu-agent/PROMPT.md」

```bash
git add drafts/ bots/ && git commit -m "chore: 第X章物理方案书"
```

---

### 第三步：执笔人（正文草稿）

**输入以下prompt：**
```
请读取以下文件内容：
- MASTER_CODEX.md
- bots/writer-agent/PROMPT.md
- drafts/0X_physics_plan.md

你的角色和指令在PROMPT.md中。
任务：根据物理方案书，写第[X]章正文草稿。
章节末尾附上更新后的状态监测。
```

**你的选择：**
- 满意 → 说「保存到drafts/0X_draft.md，进入第四步」
- 有意见 → 直接说，AI修改
- 意见是规则性的 → 说「把这条规则加进bots/writer-agent/PROMPT.md」

```bash
git add drafts/ bots/ && git commit -m "draft: 第X章初稿"
```

---

### 第四步：逻辑员（审查）

**输入以下prompt：**
```
请读取以下文件内容：
- MASTER_CODEX.md
- CHAPTER_LOG.md
- bots/logic-reviewer/PROMPT.md
- drafts/0X_draft.md

你的角色和指令在PROMPT.md中。
任务：对第[X]章草稿进行六项审查，输出审查报告。
```

**你的选择：**
- 评级A/B → 把报告里的❌发回执笔人修改，修完直接定稿
- 评级C/D → 把报告发回执笔人，说「根据审查报告重写以下段落」
- 逻辑员漏掉了某类问题 → 说「把这类检查加进bots/logic-reviewer/PROMPT.md」

循环执笔人↔逻辑员，直到评级达到A或B。

```bash
git add drafts/ && git commit -m "fix: 第X章根据审查修改"
```

---

### 收尾：定稿提交

按`CHAPTER_CHECKLIST.md`逐项打勾，然后：

```bash
mv drafts/0X_draft.md chapters/0X_chapter.md
git add .
git commit -m "release: 第X章定稿，更新世界日历和章节日志"
git checkout main
git merge chapter-[章节号]
git branch -d chapter-[章节号]
```

---

## 跳步操作（熟悉后）

场景已清楚时，可以跳过第一步直接从第二步开始。

一次触发多步：
```
完成第二步后，直接把方案书传给执笔人，输出草稿。
```

全自动触发（信任度高时）：
```
读取所有相关文件，依次以格物院→执笔人→逻辑员的角色完成第X章，
逻辑员评级B以上则输出最终草稿，低于B则自动修改后再输出。
```

---

## BOT进化记录

每次修改PROMPT.md后，在此处简单记录：

| 日期 | BOT | 修改内容 |
|---|---|---|
| 2026-03 | writer-agent | 新增：顾青情绪必须换算成具体单位 |
| 2026-03 | logic-reviewer | 新增：配角合理性检查 |

---

## 常见问题

**Q：AI读不到文件怎么办？**
直接把文件内容复制粘贴进prompt。Claude Code和Gemini CLI都支持直接粘贴大段文本。

**Q：某步输出格式不对怎么办？**
说「按照PROMPT.md要求的格式重新输出」，同时检查PROMPT.md的格式要求是否清晰。

**Q：两个AI（Claude/Gemini）输出风格不一致怎么办？**
执笔人步骤固定用一个AI，其他步骤可以混用。执笔人的风格一致性最重要。
