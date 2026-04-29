---
paths:
  - "src/translate_multi_language.py"
  - "production/quality_logs/"
  - ".claude/docs/scoring.md"
---

# Logging and Metrics Rules

## JSONL Schema Rules
- Adding any new scoring dimension or field MUST sync:
  1. `.claude/docs/scoring.md` (definition and AB mapping)
  2. JSONL schema in `.claude/docs/ops.md`
  3. `validate-jsonl.sh` (required fields list)
  4. AB report computation in `/ab-100` skill

## Quality Log Rules
- Every translation run (non-interactive) MUST write quality logs
- Each log line must be valid JSON and contain all required fields
- Log files must be append-only (never overwrite existing logs)

## Metrics Rules
- AB metrics must compare A (flags off) vs B (flags on) on the same dataset
- format_break_rate must not increase from A to B
- term_consistency must not decrease from A to B
- All metrics must be reproducible: dataset + flags → same results

## Review Gate
- Before any production run, validate log schema with validate-jsonl.sh
