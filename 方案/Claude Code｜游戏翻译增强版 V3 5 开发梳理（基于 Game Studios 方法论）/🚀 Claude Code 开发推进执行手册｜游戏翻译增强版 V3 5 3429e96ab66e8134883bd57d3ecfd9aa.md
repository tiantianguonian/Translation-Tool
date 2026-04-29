# 🚀 Claude Code 开发推进执行手册｜游戏翻译增强版 V3.5

<aside>
🎯

本页是「游戏翻译增强版 V3.5」的 Claude Code **可直接执行的推进手册**，按阶段拆解任务、明确产物、可直接复制命令到 Claude Code 执行。

上游方案文档：@d76364c290424e6890de01a4734b5047

</aside>

## 总体推进节奏（5 阶段）

| 阶段 | 名称 | 核心产物 | 预计轮次 |
| --- | --- | --- | --- |
| Phase 0 | 仓库骨架落地 | 目录 + [CLAUDE.md](http://CLAUDE.md)  • settings.json | 1～2 轮 |
| Phase 1 | 设计文档并行生成 | [prompts.md](http://prompts.md) / [glossary.md](http://glossary.md) / [scoring.md](http://scoring.md) | 3～5 轮 |
| Phase 2 | 核心功能实现 | translate_multi_[language.py](http://language.py) V3.5 | 5～10 轮 |
| Phase 3 | 测试与评测 | smoke_10_report / ab_100_report | 3～5 轮 |
| Phase 4 | 运维封装 | [ops.md](http://ops.md)  • 回退验证 + 质量日志 | 2～3 轮 |

---

## Phase 0：仓库骨架落地

### 0.1 目标

在项目根目录建立「工作室化」最小目录结构，让 Claude Code 拥有完整的记忆与规则锚点。

### 0.2 执行命令（复制到 Claude Code）

```
请帮我在当前项目根目录创建以下目录结构和文件骨架：

目录结构：
- CLAUDE.md（主入口，内容见下方模板）
- .claude/settings.json
- .claude/agents/（7 个 md 文件）
- .claude/skills/（7 个 md 文件）
- .claude/hooks/（4 个 sh 文件）
- .claude/rules/（3 个 md 文件）
- .claude/docs/（prompts.md / glossary.md / scoring.md / qa.md / ops.md，先建空文件）
- production/session-state/active.md
- production/sprints/
- production/experiments/ab-100/
- production/reports/
- production/issues/
- production/quality_logs/
- production/todo.md
- production/change_log.md
- src/（translate_multi_language.py 已存在，不覆盖）
- tests/（acceptance_check.py / smoke_10.jsonl / ab_100.jsonl，先建空文件）

所有文件内容请严格按照方案文档的模板生成，不要自由发挥。
```

### 0.3 [CLAUDE.md](http://CLAUDE.md) 内容（直接粘贴给 Claude Code）

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
- unit_talk parsing behavior must match current output
- '||' pipe-field structure must remain identical
- Cache + resume must remain
- Main concurrency model must remain

## Feature Flags
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

### 0.4 DoD 检查

- [ ]  `CLAUDE.md` 存在且包含 Non-negotiables + Feature Flags
- [ ]  `.claude/` 下 agents / skills / hooks / rules / docs 目录均已建立
- [ ]  `production/session-state/active.md` 存在
- [ ]  `production/todo.md` 存在
- [ ]  `src/translate_multi_language.py` 未被覆盖

---

## Phase 1：设计文档并行生成

<aside>
💡

这一阶段的 4 份设计文档是后续实现的「锁定依据」，必须先完成再动代码。

</aside>

### 1.1 执行顺序与命令

#### Step 1 — 运行冲刺规划

```
/translation-sprint-plan
```

> 预期产物：`production/sprints/sprint-v35-week1.md` + `production/todo.md` 更新
> 

#### Step 2 — 并行执行设计文档生成（可同时开多窗口）

```
# 窗口 A：Prompt 设计
/design-prompts target=zh-cn constraints="UI/对白/技能/任务/系统提示五类型"

# 窗口 B：术语表设计  
/design-glossary-activation

# 窗口 C：评分器设计
/design-quality-scorer
```

> 预期产物：`.claude/docs/prompts.md` / `.claude/docs/glossary.md` / `.claude/docs/scoring.md`
> 

### 1.2 各设计文档的必备内容检查

[**prompts.md](http://prompts.md) 必须包含：**

- [ ]  5 种文本类型对应的 Prompt 模板（UI / 对白 / 技能 / 任务 / 系统提示）
- [ ]  Reviewer Prompt 模板
- [ ]  「只输出译文」强约束语句
- [ ]  占位符/换行保护提醒语

[**glossary.md](http://glossary.md) 必须包含：**

- [ ]  `extract_active_terms()` 函数设计（最长匹配逻辑）
- [ ]  标点边界处理规则
- [ ]  术语缺失 issue_tag 定义
- [ ]  `ACTIVE_TERMS_LIMIT` 截断规则

[**scoring.md](http://scoring.md) 必须包含：**

- [ ]  5 维评分定义（format_score 必须为硬门槛）
- [ ]  评分公式与权重
- [ ]  pass / review / reject 三档阈值
- [ ]  issue_tags 分类法
- [ ]  AB 指标映射表

---

## Phase 2：核心功能实现

<aside>
⚠️

**规则**：所有实现必须通过 Feature Flag 控制；任何触碰结构保护逻辑的改动必须同步更新 `tests/acceptance_check.py`。

</aside>

### 2.1 实现分块顺序（严格按序，避免依赖混乱）

| 顺序 | Chunk | 命令 | 关键约束 |
| --- | --- | --- | --- |
| 1 | 文本分类器 | `/implement-v35 scope=classifier` | 失败必须回退到 text_type=normal |
| 2 | Prompt 路由 | `/implement-v35 scope=prompt_router` | 依赖 [prompts.md](http://prompts.md) 已完成 |
| 3 | 术语激活 | `/implement-v35 scope=glossary` | 依赖 [glossary.md](http://glossary.md) 已完成 |
| 4 | 质量评分器 | `/implement-v35 scope=scorer` | format_score 必须是硬门槛 |
| 5 | Reviewer 回炉 | `/implement-v35 scope=reviewer` | 必须有 MAX_REVIEW_ROUNDS 上限 |
| 6 | 质量日志 | `/implement-v35 scope=logging` | jsonl schema 须与 [scoring.md](http://scoring.md) 对齐 |
| 7 | QA 脚本 | `/implement-v35 scope=qa` | acceptance_[check.py](http://check.py) 更新 |

### 2.2 每个 Chunk 实现后的即时检查

```
# 每个 chunk 完成后立即执行结构验证
bash .claude/hooks/validate-structure.sh

# 检查 change_log 是否更新
cat production/change_log.md
```

### 2.3 全量实现完成后的回退验证（必做）

```
# 把所有 Feature Flag 设为 False，确认旧逻辑仍然正常
ENABLE_TEXT_CLASSIFIER=False \
ENABLE_REVIEWER=False \
ENABLE_TERM_CHECK=False \
python src/translate_multi_language.py --test-mode
```

- [ ]  回退模式下所有原有单测通过
- [ ]  无新增 import 导致的启动报错

---

## Phase 3：测试与评测

### 3.1 Smoke-10

```
# 确保测试数据集已准备（10 条覆盖全文本类型）
# 至少包含：UI×2 / 对白×2 / 技能×1 / 任务×1 / 系统提示×1 / unit_talk×2 / 含占位符×1

/smoke-10
```

**Smoke-10 通过标准：**

- [ ]  10 条全部通过结构安全校验（占位符 / 换行 / `||` / unit_talk）
- [ ]  `production/reports/smoke_10_report.md` 已生成
- [ ]  `production/quality_logs/smoke_10.jsonl` 已生成且每行可 parse
- [ ]  `bash .claude/hooks/validate-jsonl.sh production/quality_logs/smoke_10.jsonl` 无报错

### 3.2 AB-100

```
# 确保 tests/ab_100.jsonl 已准备（100 条，A=旧逻辑, B=新逻辑）

/ab-100
```

**AB-100 通过标准：**

- [ ]  `production/reports/ab_100_report.md` 已生成
- [ ]  B 组 format_break_rate ≤ A 组（不得回退）
- [ ]  B 组 term_consistency ≥ A 组
- [ ]  reviewer_improvement_rate_B > 0（Reviewer 有效）
- [ ]  报告包含明确的「Keep / Rollback」结论

---

## Phase 4：运维封装

### 4.1 执行命令

```
# 生成运维文档
/ops-rollout

# 验证 session-start hook 可正常恢复上下文
bash .claude/hooks/session-start.sh
```

### 4.2 [ops.md](http://ops.md) 必须包含

- [ ]  灰度策略：按文本类型上线顺序（低风险 UI → 对白 → 技能 → 高风险系统提示）
- [ ]  逐开关回退步骤（每个 Feature Flag 单独关闭的影响说明）
- [ ]  总开关回退步骤（一键切回旧逻辑）
- [ ]  质量日志聚合脚本使用说明
- [ ]  告警阈值定义（format_break_rate 上限 / reviewer_trigger_rate 上限）

---

## 完整 DoD 检查清单

### 功能层

- [ ]  文本分类可开关，失败回退 normal
- [ ]  类型化 Prompt 覆盖 UI / 对白 / 技能 / 任务 / 系统提示
- [ ]  动态术语激活 + 译后校验可开关
- [ ]  质量评分输出 5 维 + issue_tags
- [ ]  Reviewer 回炉可开关，且有最大轮数限制

### 质量层

- [ ]  任意输入不破坏占位符 / 换行 / `||` / unit_talk
- [ ]  format_score 为硬门槛（破坏则拒绝）

### 测试层

- [ ]  Smoke-10：全部通过 + 报告落盘
- [ ]  AB-100：报告落盘 + 指标脚本可复跑

### 运维层

- [ ]  quality log jsonl schema 固化 + 校验脚本
- [ ]  灰度策略文档完成
- [ ]  回退策略文档完成（逐开关 + 总开关）

---

## 快速参考：关键文件路径表

| 文件 | 职责 |
| --- | --- |
| `CLAUDE.md` | Claude Code 主入口，锁定边界与 DoD |
| `production/session-state/active.md` | 会话状态恢复锚点 |
| `production/todo.md` | 当前待办清单 |
| `production/change_log.md` | 每次实现变更记录 |
| `.claude/docs/prompts.md` | Prompt 设计文档 |
| `.claude/docs/glossary.md` | 术语激活设计文档 |
| `.claude/docs/scoring.md` | 质量评分设计文档 |
| `.claude/docs/ops.md` | 运维与灰度文档 |
| `production/reports/smoke_10_report.md` | Smoke-10 测试报告 |
| `production/reports/ab_100_report.md` | AB-100 评测报告 |
| `production/quality_logs/` | 每条翻译的质量日志（jsonl） |
| `tests/acceptance_check.py` | 结构安全验收脚本 |

---

## Hooks 快速参考

| Hook | 触发时机 | 作用 |  |  |
| --- | --- | --- | --- | --- |
| `session-start.sh` | 每次开启新会话 | 打印当前分支/实验/[active.md](http://active.md) 摘要 |  |  |
| `pre-run.sh` | 大规模翻译前 | 强制先跑 smoke-10 |  |  |
| `validate-jsonl.sh` | 生成日志后 | 校验 jsonl 每行可 parse + 字段完整 |  |  |
| `validate-structure.sh` | 每个 chunk 实现后 | 校验占位符 / 换行 / ` |  | ` 结构安全 |

<aside>
✅

**推荐执行顺序**：Phase 0 → /translation-sprint-plan → 并行 Phase 1 设计文档 → Phase 2 按 chunk 顺序实现 → Phase 3 Smoke-10 → AB-100 → Phase 4 运维封装。

每个 Phase 结束都更新 `production/session-state/active.md`，确保下次会话可无损恢复。

</aside>