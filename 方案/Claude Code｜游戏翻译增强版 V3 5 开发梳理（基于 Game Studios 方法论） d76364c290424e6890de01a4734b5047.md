# Claude Code｜游戏翻译增强版 V3.5 开发梳理（基于 Game Studios 方法论）

<aside>
🎯

目标：把现有单文件脚本 `translate_multi_language.py` 的增强需求，整理成 Claude Code 可直接执行的「工作室化项目结构 + Agent/Skill/Hook/Rule」开发方案。

</aside>

## 0. 项目定位

- 项目名：游戏翻译增强版 V3.5
- 目标文件：`translate_multi_language.py`
- 约束：单文件增量增强；保留稳定模块；所有新能力必须可开关、可灰度、可回退。

## 1. 参考框架映射（对齐 Claude Code Game Studios）

### 1.1 组件对照

- `CLAUDE.md`：项目主入口（目标、约束、目录结构、协作协议）
- `.claude/settings.json`：允许工具/命令白名单、Hook 注册、状态栏
- `.claude/agents/`：多 Agent 角色定义（分层：Director → Lead → Specialist）
- `.claude/skills/`：Slash 命令工作流（规划、实现、评测、QA、上线）
- `.claude/hooks/`：质量守卫（冒烟/AB/结构校验/日志落盘）
- `.claude/rules/`：路径级规则（本项目按“功能域/文件段落”模拟）
- `production/`：会话状态、实验记录、AB 报告、问题列表、交付物清单

### 1.2 本项目的“工作室化”最小目录（建议）

- `CLAUDE.md`
- `.claude/`
    - `settings.json`
    - `agents/`（7 个）
    - `skills/`（7 个）
    - `hooks/`（可选：3～6 个）
    - `docs/`（Prompt/术语/评分/QA/运行手册）
- `production/`
    - `session-state/active.md`
    - `experiments/ab-100/`（AB 结果与样例）
    - `reports/`（冒烟与 AB 汇总）
    - `issues/`（低分样本与术语问题归因）
- `src/`
    - `translate_multi_language.py`（或项目根目录同名文件）
- `tests/`
    - `smoke_10.jsonl`（或 csv）
    - `ab_100.jsonl`
    - `acceptance_check.py`

---

## 2. 各模块的“可直接落地”具体内容

## 2.1 `CLAUDE.md`（主入口）模板

> 这份文件的核心职责：把“边界、不可破坏项、DoD、工作流入口”写死，避免实现阶段自由发挥导致破坏稳定逻辑。参考 Game Studios 的 `CLAUDE.md` 作为“引用入口”的思路。[[1]](https://www.notion.so/Claude-Code-Game-Studios-dd5ff64e149b4e15a29a701e2272a3f9?pvs=21)
> 

```markdown
# CLAUDE.md - Game Translation Enhanced V3.5

You are the orchestrator of a game localization pipeline upgrade.
You are working on an existing single-file Python script.

## Project Identity
- Project: Game Translation Enhanced V3.5
- Target file: src/translate_multi_language.py
- Scope: incremental enhancements only (no multi-file rewrite)

## Non-negotiables (Do NOT break)
- Placeholder protection must remain 100% correct
- Newline protection must remain 100% correct
- unit_talk parsing behavior must match current output (unless a bug is confirmed)
- '||' pipe-field structure must remain identical (#fields and ordering)
- Cache + resume must remain
- Main concurrency model must remain (unless explicitly gated for reviewer)

## Feature Flags (all new features must be gated)
- ENABLE_TEXT_CLASSIFIER
- ENABLE_REVIEWER
- ENABLE_TERM_CHECK
- PASS_SCORE_THRESHOLD
- REVIEW_SCORE_THRESHOLD
- MAX_REVIEW_ROUNDS
- ACTIVE_TERMS_LIMIT
- HIGH_RISK_TYPES
- DEBUG_TOP_N

## Key Docs (file-backed memory)
@production/session-state/active.md
@.claude/docs/prompts.md
@.claude/docs/glossary.md
@.claude/docs/scoring.md
@.claude/docs/qa.md
@.claude/docs/ops.md

## Definition of Done
- Smoke-10 passes with structure safety checks
- AB-100 report generated with metrics
- Quality log schema fixed + samples produced
- Rollback plan validated (feature flags off still runs)

## Workflow Entrypoints
- /translation-sprint-plan
- /implement-v35
- /smoke-10
- /ab-100
```

---

## 2.2 `.claude/agents/`（Agent 定义）——7 个文件模板

> 统一前置：每个 Agent 都强调“输出契约”，并把“不可破坏项”作为硬约束。分层思路来自 Game Studios：决策/负责人/专家分离。[[1]](https://www.notion.so/Claude-Code-Game-Studios-dd5ff64e149b4e15a29a701e2272a3f9?pvs=21)
> 

### 2.2.1 `planner-agent.md`

```yaml
---
name: planner-agent
description: "Decompose V3.5 requirements into a 1-week incremental plan with deliverables and acceptance criteria."
tools: Read, Glob, Grep, Write, Edit
model: sonnet
maxTurns: 20
memory: user
skills:
  - translation-sprint-plan
---
```

正文建议（摘）

- 输出必须包含：scope / constraints / modules / execution_order / deliverables / acceptance_criteria
- 遇到不确定：先定义“可回退”的最小版本，再扩展

### 2.2.2 `implementation-agent.md`

```yaml
---
name: implementation-agent
description: "Implement V3.5 in a single-file Python script with minimal refactor and feature flags."
tools: Read, Glob, Grep, Write, Edit, Bash
model: sonnet
maxTurns: 30
memory: user
skills:
  - implement-v35
---
```

正文建议（摘）

- 只能做“增量改造”，优先加函数/分支，不做大重构
- 任何新逻辑必须通过 config flag 控制
- 任何触碰结构保护逻辑的改动必须同步更新 acceptance_check

### 2.2.3 `prompt-agent.md`

```yaml
---
name: prompt-agent
description: "Design typed prompts and reviewer prompts for game localization, enforce formatting and terminology."
tools: Read, Write, Edit
model: sonnet
maxTurns: 20
memory: user
skills:
  - design-prompts
---
```

### 2.2.4 `glossary-agent.md`

```yaml
---
name: glossary-agent
description: "Design active-term extraction and deterministic terminology validation rules."
tools: Read, Write, Edit
model: sonnet
maxTurns: 20
memory: user
skills:
  - design-glossary-activation
---
```

### 2.2.5 `evaluation-agent.md`

```yaml
---
name: evaluation-agent
description: "Design heuristic multi-dimensional quality scoring and thresholds for pass/review decisions."
tools: Read, Write, Edit
model: sonnet
maxTurns: 20
memory: user
skills:
  - design-quality-scorer
---
```

### 2.2.6 `qa-agent.md`

```yaml
---
name: qa-agent
description: "Define smoke tests, AB requirements, structure safety checks, and fail conditions."
tools: Read, Glob, Grep, Write, Edit, Bash
model: sonnet
maxTurns: 25
memory: user
skills:
  - smoke-10
  - ab-100
---
```

### 2.2.7 `ops-agent.md`

```yaml
---
name: ops-agent
description: "Define quality logs, aggregation, rollout, and rollback plan for V3.5."
tools: Read, Write, Edit, Bash
model: sonnet
maxTurns: 20
memory: user
skills:
  - ops-rollout
---
```

---

## 2.3 `.claude/skills/`（Slash 工作流）——7 个技能模板

> 每个 Skill 都是一条“可重复执行的 SOP”，强调输入输出与落盘文件位置。
> 

### 2.3.1 `/translation-sprint-plan`

```yaml
---
name: translation-sprint-plan
description: "Create a 1-week incremental plan for V3.5 with deliverables and risk controls."
argument-hint: "[optional focus: classifier|prompts|glossary|scoring|reviewer|qa|ops]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit
---
```

输出契约：

- 写入 `production/sprints/sprint-v35-week1.md`
- 更新 `production/todo.md`

### 2.3.2 `/design-prompts`

```yaml
---
name: design-prompts
description: "Generate typed prompt templates + reviewer prompt, with strict formatting rules."
argument-hint: "[target language + constraints]"
user-invocable: true
allowed-tools: Read, Write, Edit
---
```

输出契约：

- 写入 `.claude/docs/prompts.md`

### 2.3.3 `/design-glossary-activation`

```yaml
---
name: design-glossary-activation
description: "Define active-term extraction and deterministic term validation, plus term issue tags."
user-invocable: true
allowed-tools: Read, Write, Edit
---
```

输出契约：

- 写入 `.claude/docs/glossary.md`

### 2.3.4 `/design-quality-scorer`

```yaml
---
name: design-quality-scorer
description: "Define scoring dimensions, formula, thresholds, issue tags, and AB metrics mapping."
user-invocable: true
allowed-tools: Read, Write, Edit
---
```

输出契约：

- 写入 `.claude/docs/scoring.md`

### 2.3.5 `/implement-v35`

```yaml
---
name: implement-v35
description: "Implement V3.5 behind flags in translate_multi_language.py, and add quality logging."
argument-hint: "[scope chunk: classifier|prompt_router|glossary|scorer|reviewer|logging|qa]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---
```

输出契约：

- 修改 `src/translate_multi_language.py`
- 写入 `production/change_log.md`

### 2.3.6 `/smoke-10`

```yaml
---
name: smoke-10
description: "Run smoke test on 10 samples with structure safety checks and output report."
user-invocable: true
allowed-tools: Read, Write, Edit, Bash
---
```

输出契约：

- 生成 `reports/smoke_10_report.md`
- 生成 `production/quality_logs/smoke_10.jsonl`

### 2.3.7 `/ab-100`

```yaml
---
name: ab-100
description: "Run AB test on 100 samples (A=baseline, B=enhanced) and output metrics report."
user-invocable: true
allowed-tools: Read, Write, Edit, Bash
---
```

输出契约：

- 生成 `reports/ab_100_report.md`
- 生成 `production/quality_logs/ab_100_A.jsonl` / `ab_100_B.jsonl`

---

## 2.4 `.claude/hooks/`（Hook 守卫）——最小可用 4 个

> Hook 的模式参考 Game Studios：在关键节点自动执行校验与状态落盘。[[1]](https://www.notion.so/Claude-Code-Game-Studios-dd5ff64e149b4e15a29a701e2272a3f9?pvs=21)
> 

### 2.4.1 `session-start.sh`

职责：输出当前分支/最近实验/[active.md](http://active.md) 摘要，用于恢复上下文。

### 2.4.2 `pre-run.sh`

职责：跑任何大规模翻译前强制先跑 smoke-10。

### 2.4.3 `validate-jsonl.sh`

职责：校验质量日志 jsonl 每行可 parse + 必备字段齐全（防止日志闭环断裂）。

### 2.4.4 `validate-structure.sh`

职责：校验“占位符/换行/`||`”结构安全（对 smoke 与 AB 共用）。

> 备注：具体脚本实现可以极简，只要把失败 exit code 用起来即可。
> 

---

## 2.5 `.claude/rules/`（规则）——按“逻辑域”约束变更

> Game Studios 用 paths 约束目录；本项目单文件，改用“段落域/职责域”模拟。[[1]](https://www.notion.so/Claude-Code-Game-Studios-dd5ff64e149b4e15a29a701e2272a3f9?pvs=21)
> 

### 2.5.1 `translation-core.md`（结构保护域）

```markdown
---
paths:
  - "src/translate_multi_language.py"
---

# Translation Core Safety Rules

## Non-negotiables
- Any change touching placeholder/newline/pipe-field logic MUST update tests/acceptance_check.py
- Any change touching unit_talk parsing MUST add at least one smoke sample covering unit_talk

## Review Gate
- format_score must be a hard gate: if broken, translation is rejected regardless of other scores
```

### 2.5.2 `prompts-and-style.md`

- 新增/修改 prompt 模板必须同步更新 `.claude/docs/prompts.md`
- prompt 必须包含“只输出译文”的强约束

### 2.5.3 `logging-and-metrics.md`

- 新增任何评分维度/字段，必须同步：jsonl schema + AB 统计脚本

---

## 2.6 `production/`（文件支撑的“长期记忆”）模板

> 参考 Game Studios 的 session-state 方案：把进度写进文件，避免上下文压缩损失。[[1]](https://www.notion.so/Claude-Code-Game-Studios-dd5ff64e149b4e15a29a701e2272a3f9?pvs=21)
> 

### 2.6.1 `production/session-state/active.md`

```markdown
# Active State (V3.5)

## Current Objective
- Implement: [e.g. reviewer loop + scoring integration]

## Decisions Locked
- format_score is hard gate
- reviewer only runs for high-risk types or low score

## Open Questions
- glossary longest-match: punctuation handling?

## Next Actions
- [ ] Implement extract_active_terms()
- [ ] Add issue_tags taxonomy
- [ ] Update acceptance_check.py
```

### 2.6.2 `production/todo.md`

```markdown
# TODO
- [ ] Smoke-10 dataset finalized
- [ ] AB-100 dataset finalized
- [ ] Quality log schema frozen
- [ ] Rollback verification (all flags off)
```

### 2.6.3 `production/reports/smoke_10_report.md`（模板）

```markdown
# Smoke-10 Report

## Summary
- pass_count:
- fail_count:

## Fail Reasons (top)
- placeholder_break:
- newline_break:
- pipe_field_break:
- term_miss:

## Samples
- sample_id:
  - type:
  - issues:
  - notes:
```

### 2.6.4 `production/reports/ab_100_report.md`（模板）

```markdown
# AB-100 Report

## Metrics
- success_rate_A / success_rate_B
- format_break_rate_A / _B
- term_consistency_A / _B
- reviewer_trigger_rate_B
- reviewer_improvement_rate_B

## Conclusion
- Keep / rollback recommendation:

## Top regressions
- ...
```

---

## 3. DoD（Definition of Done）——更细的可勾选清单

- 功能层
    - [ ]  文本分类可开关，失败回退 normal
    - [ ]  类型化 Prompt 覆盖 UI/对白/技能/任务/系统提示
    - [ ]  动态术语激活 + 译后校验可开关
    - [ ]  质量评分输出 5 维 + issue_tags
    - [ ]  reviewer 回炉可开关，且有最大轮数限制
- 质量层
    - [ ]  任意输入不破坏占位符/换行/`||`/`unit_talk`
    - [ ]  format_score 为硬门槛（破坏则拒绝）
- 测试层
    - [ ]  Smoke-10：全部通过 + 报告落盘
    - [ ]  AB-100：报告落盘 + 指标脚本可复跑
- 运维层
    - [ ]  quality log jsonl schema 固化 + 校验脚本
    - [ ]  灰度策略文档完成（按类型上线顺序）
    - [ ]  回退策略文档完成（逐开关/总开关）

---

## 4. 流程编排（把“translate() 链路”固化为执行流程）

```mermaid
flowchart TD
	A[Input text] --> B[Preprocess: placeholder/newline/unit_talk/||]
	B --> C{ENABLE_TEXT_CLASSIFIER?}
	C -- yes --> D[Classify: text_type + risk_level]
	C -- no --> E[text_type=normal]
	D --> F
	E --> F
	F{ENABLE_TERM_CHECK?} -- yes --> G[Extract active_terms]
	F{ENABLE_TERM_CHECK?} -- no --> H[active_terms=[]]
	G --> I
	H --> I
	I[Build typed prompt] --> J[Draft translation]
	J --> K[Clean / postprocess]
	K --> L[Score draft]
	L --> M{Need reviewer?}
	M -- no --> N[Select draft]
	M -- yes --> O[Reviewer prompt repair]
	O --> P[Score reviewed]
	P --> Q[Select best]
	N --> R[Cache + resume]
	Q --> R
	R --> S[Write quality log jsonl]
	S --> T[Output]
```

---

## 5. 主流程编排（translate() 的可视化链路，代码侧检查点）

1. 预处理：占位符保护 / 换行保护 / `unit_talk` / `||`（沿用旧逻辑）
2. 分类：`text_type = classify()`（可开关）
3. 术语激活：`active_terms = extract_active_terms()`（可开关）
4. 首译：`draft = translate_once(prompt)`
5. 清洗：沿用旧逻辑
6. 评分：`score_draft = score(draft)`
7. Reviewer：若触发 → `reviewed = review(draft)` → `score_reviewed = score(reviewed)`
8. 选优：`best = select_best(draft, reviewed)`
9. 缓存/断点续跑：沿用旧逻辑
10. 质量日志：每条落盘（jsonl），并生成聚合统计（AB/冒烟）

<aside>
✅

以上模块补全后，你就可以把仓库按这些文件落地，然后让 Claude Code 以“读 [CLAUDE.md](http://CLAUDE.md) → 跑 /translation-sprint-plan → 并行 design skills → /implement-v35 → /smoke-10 → /ab-100”的顺序推进。

</aside>

[🚀 Claude Code 开发推进执行手册｜游戏翻译增强版 V3.5](Claude%20Code%EF%BD%9C%E6%B8%B8%E6%88%8F%E7%BF%BB%E8%AF%91%E5%A2%9E%E5%BC%BA%E7%89%88%20V3%205%20%E5%BC%80%E5%8F%91%E6%A2%B3%E7%90%86%EF%BC%88%E5%9F%BA%E4%BA%8E%20Game%20Studios%20%E6%96%B9%E6%B3%95%E8%AE%BA%EF%BC%89/%F0%9F%9A%80%20Claude%20Code%20%E5%BC%80%E5%8F%91%E6%8E%A8%E8%BF%9B%E6%89%A7%E8%A1%8C%E6%89%8B%E5%86%8C%EF%BD%9C%E6%B8%B8%E6%88%8F%E7%BF%BB%E8%AF%91%E5%A2%9E%E5%BC%BA%E7%89%88%20V3%205%203429e96ab66e8134883bd57d3ecfd9aa.md)