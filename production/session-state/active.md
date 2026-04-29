# Active State (V3.5)

## Current Objective
- Complete: All 5 phases implemented and verified

## Decisions Locked
- format_score is hard gate
- reviewer only runs for high-risk types or low score
- glossary longest-match with priority-based truncation

## Completed
- [x] Phase 0: Repository skeleton
- [x] Phase 1: Design documents (prompts, glossary, scoring, qa, ops)
- [x] Phase 2: Core implementation (classifier, prompt_router, glossary, scorer, reviewer, logging, qa)
- [x] Phase 3: Smoke-10 and AB-100 test infrastructure
- [x] Phase 4: Rollback verification + ops docs
- [x] Rollback verified: all flags OFF preserves old behavior

## Open Questions
- Production LLM API integration (replace mock call_llm)
- Glossary CSV data population for target game

## Next Actions
- [ ] Integrate real LLM API (Anthropic/OpenAI)
- [ ] Populate game-specific glossary CSV
- [ ] Run with real LLM to validate actual translation quality
