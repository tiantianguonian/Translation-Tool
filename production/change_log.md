# Change Log

## 2026-04-29 — Phase 0: Repository Skeleton
- Created full directory structure
- Added CLAUDE.md, settings.json
- Created all agent/skill/hook/rule scaffolds
- Initialized production tracking files

## 2026-04-29 — Phase 1: Design Documents
- Filled `.claude/docs/prompts.md` with 5 typed prompt templates + reviewer prompt
- Filled `.claude/docs/glossary.md` with longest-match extraction algorithm
- Filled `.claude/docs/scoring.md` with 5-dimension scoring + issue_tags taxonomy
- Filled `.claude/docs/qa.md` with test procedures and fail conditions
- Filled `.claude/docs/ops.md` with canary strategy, rollback, and alert thresholds
- Created `production/sprints/sprint-v35-week1.md`

## 2026-04-29 — Phase 2: Core Implementation
- Added text classifier (`classify()`, `_classify_by_patterns()`) — flagged: ENABLE_TEXT_CLASSIFIER
- Added prompt router (`build_typed_prompt()`, 6 prompt templates) — depends on ENABLE_TEXT_CLASSIFIER
- Added glossary activation (`load_glossary()`, `extract_active_terms()`, `validate_terms()`) — flagged: ENABLE_TERM_CHECK
- Added quality scorer (`score_translation()`, 5 dimensions, format_score hard gate) — always on
- Added reviewer loop (`review_and_repair()`, `needs_reviewer()`, `select_best()`) — flagged: ENABLE_REVIEWER
- Added quality logging (`write_quality_log()`) — JSONL schema aligned with scoring.md
- Updated main `translate()` pipeline with all 11 steps
- Added CLI with argument parsing
- Added self-tests covering classification, structure protection, scoring, glossary

## 2026-04-29 — Phase 3: Test Infrastructure
- Created `tests/run_smoke_10.py` — 10-sample smoke test runner
- Created `tests/run_ab_100.py` — 100-sample AB evaluation runner
- Populated `tests/smoke_10.jsonl` with 10 diverse samples
- AB-100 demo sample generation for testing
- Generated `production/reports/smoke_10_report.md`
- Generated `production/reports/ab_100_report.md`
- Quality logs validated with validate-jsonl.sh hook

## 2026-04-29 — Phase 4: Operations & Rollback
- Rollback verified: all flags OFF → old behavior preserved
- JSONL validation hook operational
- Session-start hook operational
- Structure validation hook operational
- Ops.md includes canary strategy, per-flag rollback, master switch rollback, alert thresholds
