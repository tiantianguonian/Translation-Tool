---
name: smoke-10
description: "Run smoke test on 10 samples with structure safety checks and output report."
user-invocable: true
allowed-tools: Read, Write, Edit, Bash
---

# /smoke-10

Execute the Smoke-10 test suite against the current V3.5 implementation.

## Input
- Read `tests/smoke_10.jsonl` (10 test samples)
- Read `tests/acceptance_check.py`

## Process
1. Load 10 samples from `tests/smoke_10.jsonl`
2. For each sample:
   a. Run through translate() with all feature flags ENABLED
   b. Run structure safety checks (placeholder, newline, pipe, unit_talk)
   c. Record format_score, all dimension scores, issue_tags, verdict
   d. Write quality log entry
3. Aggregate results:
   - pass_count / fail_count
   - Fail reasons breakdown (placeholder_break, newline_break, pipe_field_break, term_miss)
   - Per-sample detail (sample_id, type, issues, notes)
4. Validate output: `bash .claude/hooks/validate-jsonl.sh production/quality_logs/smoke_10.jsonl`

## Pass Criteria (hard)
- ALL 10 samples pass structure safety checks
- At least 8/10 pass quality scoring (PASS_SCORE_THRESHOLD)
- Report generated
- JSONL valid

## Output Contract
- Write `production/reports/smoke_10_report.md`
- Write `production/quality_logs/smoke_10.jsonl`
