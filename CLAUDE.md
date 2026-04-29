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
