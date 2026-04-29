# Ops — Game Translation V3.5

> Operations manual: quality logging, canary rollout, rollback procedures, alert thresholds.

## Quality Log Schema (JSONL)

Each translation produces one JSON line with the following schema:

```json
{
  "timestamp": "2026-04-29T10:30:00Z",
  "sample_id": "string",
  "text_type": "UI|dialogue|skill|quest|system|normal",
  "source_text": "string (truncated to 200 chars)",
  "translated_text": "string (truncated to 200 chars)",
  "format_score": 0.0|1.0,
  "term_consistency": 0.0-1.0,
  "fluency": 0.0-1.0,
  "completeness": 0.0-1.0,
  "style_match": 0.0-1.0,
  "final_score": 0.0-1.0,
  "verdict": "PASS|REVIEW|REJECT",
  "reviewer_used": true|false,
  "review_rounds": 0-N,
  "active_terms": ["term1", "term2"],
  "issue_tags": ["tag1", "tag2"],
  "config_flags": {
    "ENABLE_TEXT_CLASSIFIER": true,
    "ENABLE_REVIEWER": true,
    "ENABLE_TERM_CHECK": true
  }
}
```

## Canary Rollout Strategy

Roll out features by text type, lowest risk first:

### Week 1: UI only
- `ENABLE_TEXT_CLASSIFIER=True`, `ENABLE_TERM_CHECK=True`
- `HIGH_RISK_TYPES=["system"]` (system messages use old path)
- Monitor: format_break_rate, success_rate on UI corpus

### Week 2: + Dialogue
- Add dialogue to classifier and term check
- Monitor: style_match scores, reviewer_trigger_rate

### Week 3: + Skill + Quest
- Full gameplay text coverage
- Monitor: term_consistency (gameplay terms are critical)

### Week 4: + System (full rollout)
- `HIGH_RISK_TYPES=[]` (all types use new path)
- `ENABLE_REVIEWER=True`
- Monitor all metrics; prepare rollback if format_break_rate > 0.01

## Per-Flag Rollback

| Flag Change | Impact |
|-------------|--------|
| `ENABLE_TEXT_CLASSIFIER=False` | All text → type=normal; typed prompts disabled; fallback to general prompt |
| `ENABLE_TERM_CHECK=False` | No glossary extraction; no term validation; term_consistency score skipped (1.0 default) |
| `ENABLE_REVIEWER=False` | No repair loop; draft used directly if score passes; review verdict becomes WARN instead of REJECT |

## Master Switch Rollback

Set all flags to False to fully revert to baseline:

```bash
python -c "
from src.translate_multi_language import CONFIG
CONFIG['ENABLE_TEXT_CLASSIFIER'] = False
CONFIG['ENABLE_REVIEWER'] = False
CONFIG['ENABLE_TERM_CHECK'] = False
# Old translate() path is fully active
print('Rollback verified: all flags OFF')
"
```

### Rollback Verification Checklist
- [ ] All existing unit tests pass
- [ ] No import errors on startup
- [ ] Cache and resume work correctly
- [ ] Smoke-10 passes on baseline (old logic)
- [ ] Output format identical to pre-V3.5

## Quality Log Aggregation

Use the aggregation script for periodic reports:

```python
# Aggregate quality logs and compute summary metrics
python -c "
import json, sys, glob
from collections import Counter

logs = []
for f in glob.glob('production/quality_logs/*.jsonl'):
    with open(f) as fh:
        for line in fh:
            if line.strip():
                logs.append(json.loads(line))

total = len(logs)
pass_count = sum(1 for l in logs if l['verdict'] == 'PASS')
reject_count = sum(1 for l in logs if l['verdict'] == 'REJECT')
review_count = sum(1 for l in logs if l['verdict'] == 'REVIEW')
avg_score = sum(l['final_score'] for l in logs) / max(total, 1)
format_breaks = sum(1 for l in logs if l['format_score'] == 0)
issue_freq = Counter(tag for l in logs for tag in l['issue_tags'])

print(f'Total: {total} | Pass: {pass_count} ({pass_count/total*100:.1f}%)')
print(f'Review: {review_count} | Reject: {reject_count}')
print(f'Avg Score: {avg_score:.3f} | Format Breaks: {format_breaks}')
print(f'Top Issues: {issue_freq.most_common(5)}')
"
```

## Alert Thresholds

| Alert | Threshold | Action |
|-------|-----------|--------|
| **CRITICAL: Format Break** | `format_break_rate > 0.01` (1%) | Immediate rollback, investigate all failures |
| **WARN: High Review Rate** | `reviewer_trigger_rate > 0.50` (50%) | Too many translations need repair; investigate prompt/scorer calibration |
| **WARN: Low Avg Score** | `avg_final_score < 0.6` | Scorer or translation quality issue |
| **INFO: Smoke Fail** | Any smoke-10 failure | BLOCK next canary phase until resolved |
