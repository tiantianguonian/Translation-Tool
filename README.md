# 游戏翻译增强版 V3.5

基于 Claude Code Game Studios 方法论构建的游戏本地化翻译管线。

## 项目结构

```
├── CLAUDE.md                          # 项目主入口（目标、约束、Feature Flags、DoD）
├── README.md                          # 本文件
├── .claude/
│   ├── settings.json                  # 工具白名单、Hook 注册、状态栏配置
│   ├── agents/                        # 7 个 Agent 角色定义
│   │   ├── planner-agent.md           # 冲刺规划 Agent
│   │   ├── implementation-agent.md    # 代码实现 Agent
│   │   ├── prompt-agent.md            # Prompt 设计 Agent
│   │   ├── glossary-agent.md          # 术语表设计 Agent
│   │   ├── evaluation-agent.md        # 评分器设计 Agent
│   │   ├── qa-agent.md               # 测试与质量保障 Agent
│   │   └── ops-agent.md              # 运维与上线 Agent
│   ├── skills/                        # 7 个 Slash 命令工作流
│   │   ├── translation-sprint-plan.md # 冲刺规划技能
│   │   ├── design-prompts.md          # Prompt 设计技能
│   │   ├── design-glossary-activation.md # 术语激活设计技能
│   │   ├── design-quality-scorer.md   # 评分器设计技能
│   │   ├── implement-v35.md           # 核心功能实现技能
│   │   ├── smoke-10.md               # 冒烟测试技能
│   │   └── ab-100.md                 # AB 评测技能
│   ├── hooks/                         # 质量守卫 Hook 脚本
│   │   ├── session-start.sh           # 会话启动：打印上下文摘要
│   │   ├── pre-run.sh                # 大规模翻译前强制检验
│   │   ├── validate-jsonl.sh          # JSONL 日志格式校验
│   │   └── validate-structure.sh      # 结构安全校验（占位符/换行/管道）
│   ├── rules/                         # 路径级规则（按功能域约束变更）
│   │   ├── translation-core.md        # 核心结构保护规则
│   │   ├── prompts-and-style.md       # Prompt 与风格规则
│   │   └── logging-and-metrics.md     # 日志与指标规则
│   └── docs/                          # 设计文档（实现前锁定）
│       ├── prompts.md                 # 5 种文本类型的 Prompt 模板 + Reviewer Prompt
│       ├── glossary.md                # 术语提取算法、边界处理、校验规则
│       ├── scoring.md                 # 5 维评分体系、issue_tags 分类法、AB 指标映射
│       ├── qa.md                     # 测试数据集要求、冒烟/AB 流程、失败条件
│       └── ops.md                    # 灰度策略、回退方案、告警阈值、质量日志聚合
├── src/
│   └── translate_multi_language.py    # 主翻译脚本（单文件增量增强）
├── tests/
│   ├── acceptance_check.py            # 结构安全验收脚本（占位符/换行/管道/unit_talk）
│   ├── run_smoke_10.py               # 10 样本冒烟测试执行器
│   ├── run_ab_100.py                 # 100 样本 AB 评测执行器
│   ├── smoke_10.jsonl                # 冒烟测试数据集（覆盖全部 5 种文本类型）
│   └── ab_100.jsonl                  # AB 评测数据集
└── production/
    ├── session-state/active.md        # 当前会话状态（上下文恢复锚点）
    ├── todo.md                        # 待办清单
    ├── change_log.md                  # 实现变更记录
    ├── sprints/                       # 冲刺规划文档
    ├── reports/                       # 测试报告（smoke_10 + ab_100）
    ├── quality_logs/                  # JSONL 质量日志
    ├── experiments/                   # 实验记录
    └── issues/                        # 问题归因记录
```

## 核心功能

整个翻译管线由以下模块组成，所有新功能均通过 **Feature Flag** 控制，默认关闭，可灰度、可回退：

| 模块 | Feature Flag | 功能 |
|------|-------------|------|
| 结构化保护 | 始终启用 | 占位符 `{0}` / 换行 `\n` / 管道 `\|\|` / `unit_talk` 标签保护 |
| 文本分类器 | `ENABLE_TEXT_CLASSIFIER` | 将文本分为 UI/对白/技能/任务/系统提示 5 类 |
| 类型化 Prompt | `ENABLE_TEXT_CLASSIFIER` | 根据文本类型路由到对应的 Prompt 模板 |
| 术语激活 | `ENABLE_TERM_CHECK` | 最长匹配提取活跃术语，译后校验术语一致性 |
| 质量评分 | 始终启用 | 5 维评分（格式/术语/流畅度/完整性/风格），格式分为硬门槛 |
| Reviewer 回炉 | `ENABLE_REVIEWER` | 低分译文自动进入修复循环，有最大轮次上限 |
| 质量日志 | 始终启用 | 每条译文落盘 JSONL，含全维度评分和 issue_tags |

### Feature Flags 一览

| Flag | 默认值 | 说明 |
|------|--------|------|
| `ENABLE_TEXT_CLASSIFIER` | False | 启用文本类型分类 |
| `ENABLE_REVIEWER` | False | 启用 Reviewer 修复循环 |
| `ENABLE_TERM_CHECK` | False | 启用术语表激活与校验 |
| `PASS_SCORE_THRESHOLD` | 0.7 | 自动通过的分数门槛 |
| `REVIEW_SCORE_THRESHOLD` | 0.5 | 触发 Reviewer 的分数门槛 |
| `MAX_REVIEW_ROUNDS` | 3 | Reviewer 最大修复轮次 |
| `ACTIVE_TERMS_LIMIT` | 20 | 每条文本最多激活术语数 |
| `HIGH_RISK_TYPES` | ["system"] | 高风险文本类型（强制走 Reviewer） |
| `DEBUG_TOP_N` | 0 | 调试模式：限制处理条数 |

## 使用说明

### 环境要求

- Python 3.10+
- Bash（用于 Hook 脚本）

### 快速开始

```bash
# 1. 运行所有自测
python src/translate_multi_language.py --self-test
python tests/acceptance_check.py --self-test

# 2. 单条翻译（基础模式，所有 Flag 关闭）
python src/translate_multi_language.py --text "Start Game"

# 3. 单条翻译（启用分类器）
python src/translate_multi_language.py --text "Fire Ball - Deals 100 damage" --enable-classifier

# 4. 单条翻译（全功能开启）
python src/translate_multi_language.py --text "Hello {0}" \
    --enable-classifier --enable-reviewer --enable-term-check \
    --source-lang en --target-lang zh-cn

# 5. 批量翻译（JSONL 输入）
python src/translate_multi_language.py --input tests/smoke_10.jsonl --enable-classifier

# 6. 指定术语表
python src/translate_multi_language.py --text "Fire Ball" \
    --glossary path/to/glossary.csv --enable-term-check
```

### 术语表格式（CSV）

```csv
source_term,target_term,text_type,priority
Fire Ball,火球术,skill,1
Ice Golem,冰魔像,skill,2
Frozen Cave,冰窟,*,3
```

- `text_type`：适用的文本类型，`*` 表示全部
- `priority`：1~5，数字越小优先级越高

### 运行测试

```bash
# 冒烟测试（10 条样本）
python tests/run_smoke_10.py

# AB 评测（100 条样本，A=基准 / B=增强）
python tests/run_ab_100.py

# 查看测试报告
cat production/reports/smoke_10_report.md
cat production/reports/ab_100_report.md

# 校验质量日志格式
bash .claude/hooks/validate-jsonl.sh production/quality_logs/smoke_10.jsonl

# 结构安全校验
bash .claude/hooks/validate-structure.sh
```

### 回退操作

```bash
# 所有 Flag 设为 False 即可回退到旧版行为
python src/translate_multi_language.py --text "Hello {0}"  # 不加任何 --enable-* 参数
```

## 质量评分体系

每条译文经过 5 个维度评分：

| 维度 | 权重 | 说明 |
|------|------|------|
| format_score | 硬门槛 | 占位符/换行/管道/unit_talk 结构完整性（失败则直接 REJECT） |
| term_consistency | 0.25 | 术语翻译一致性 |
| fluency | 0.25 | 译文流畅度 |
| completeness | 0.25 | 译文完整度 |
| style_match | 0.25 | 文本类型风格匹配度 |

## 不可破坏项（Non-negotiables）

- 占位符保护（`{0}`、`%s`、`{name}` 等）
- 换行符保护（`\n`、`\r\n`）
- `unit_talk` 标签解析行为
- `||` 管道字段结构（字段数和顺序）
- 缓存与断点续跑
- 主并发模型

## License

Internal project — Game Translation Enhanced V3.5
