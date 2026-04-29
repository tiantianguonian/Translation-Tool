# QA — Game Translation V3.5

> Quality assurance procedures: test datasets, smoke tests, AB evaluation, and failure handling.

## Test Datasets

### smoke_10.jsonl
- 10 samples, manually curated
- Coverage: UI×2, Dialogue×2, Skill×1, Quest×1, System×1, unit_talk×2, placeholder×1
- Each sample must have a known-good expected output for structure validation

### ab_100.jsonl
- 100 samples, balanced distribution
- 20 each: UI, Dialogue, Skill, Quest, System
- Must include edge cases: placeholders, newlines, pipes, unit_talk, CJK-heavy, emoji, mixed script

## Structure Safety Checks (acceptance_check.py)

Run before every test suite execution:

```python
def check_placeholder_identity(source: str, target: str) -> bool:
    """All placeholders in source must exist in target."""
    
def check_placeholder_count(source: str, target: str) -> bool:
    """Same number of each placeholder type."""
    
def check_newline_count(source: str, target: str) -> bool:
    """Same number of \n newlines."""
    
def check_pipe_fields(source: str, target: str) -> bool:
    """Same number of ||-separated fields."""
    
def check_unit_talk(source: str, target: str) -> bool:
    """All [unit_talk:XXX] tags preserved exactly."""
```

## Smoke-10 Procedure
1. Load `tests/smoke_10.jsonl`
2. Run translate() with ALL feature flags ON
3. For each sample, run structure safety checks
4. Record all scores, issue_tags, verdict
5. Generate report and quality log
6. Validate JSONL output

## AB-100 Procedure
1. Load `tests/ab_100.jsonl`
2. Run A (baseline, all flags OFF) → `ab_100_A.jsonl`
3. Run B (enhanced, all flags ON) → `ab_100_B.jsonl`
4. Compute all 5 metrics for both groups
5. Compare and generate Keep/Rollback recommendation

## Fail Conditions
| Condition | Severity | Action |
|-----------|----------|--------|
| Any format_score==0 in smoke-10 | CRITICAL | BLOCK deployment |
| Smoke-10 report not generated | HIGH | INCOMPLETE |
| AB-100 B format_break_rate > A | HIGH | ROLLBACK |
| AB-100 reviewer_improvement_rate == 0 | MEDIUM | INVESTIGATE |
| JSONL validation fails | HIGH | FIX SCHEMA |
