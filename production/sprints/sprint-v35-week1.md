# Sprint V3.5 Week 1 Plan

## Scope
Incremental enhancement of `src/translate_multi_language.py` with 5 new capabilities:
1. Text classifier (text_type + risk_level)
2. Typed prompt routing (5 game text types)
3. Dynamic glossary activation + term validation
4. Multi-dimensional quality scoring (5 dimensions)
5. Reviewer repair loop

## Constraints
- Single-file enhancement only
- All new features behind feature flags (default OFF)
- Non-negotiables preserved (placeholder, newline, pipe, unit_talk, cache, concurrency)
- format_score is hard gate

## Modules

| # | Module | Feature Flag | Depends On | Agent |
|---|--------|-------------|------------|-------|
| 1 | Text Classifier | ENABLE_TEXT_CLASSIFIER | — | implementation-agent |
| 2 | Prompt Router | ENABLE_TEXT_CLASSIFIER | module 1, prompts.md | implementation-agent |
| 3 | Glossary Activation | ENABLE_TERM_CHECK | glossary.md | implementation-agent |
| 4 | Quality Scorer | — (always on for logging) | scoring.md | implementation-agent |
| 5 | Reviewer Loop | ENABLE_REVIEWER | module 4 | implementation-agent |
| 6 | Quality Logging | — (always on) | module 4 | implementation-agent |
| 7 | QA Scripts | — | all modules | qa-agent |

## Execution Order
1. classifier → 2. prompt_router → 3. glossary → 4. scorer → 5. reviewer → 6. logging → 7. qa

## Deliverables
- `src/translate_multi_language.py` (enhanced)
- `tests/acceptance_check.py` (updated)
- `production/change_log.md` (per-chunk entries)
- `production/quality_logs/*.jsonl` (test outputs)

## Acceptance Criteria
- [ ] All feature flags OFF → old behavior fully preserved
- [ ] Smoke-10: all 10 pass structure safety
- [ ] AB-100: B format_break_rate ≤ A; B term_consistency ≥ A
- [ ] reviewer_improvement_rate_B > 0
- [ ] Rollback verification passes
