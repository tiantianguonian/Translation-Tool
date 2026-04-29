# Scoring — Game Translation V3.5

> Design document for the 5-dimension heuristic quality scoring system.

## Scoring Dimensions

### 1. format_score (HARD GATE)
**Weight**: Critical (not included in composite; gates all other scores)
**Type**: Binary — 1.0 (pass) or 0.0 (fail)

Check:
- Placeholder count match: `count_placeholders(source) == count_placeholders(translation)`
- Placeholder identity match: every `{N}`, `%s`, `{name}` etc. in source is present in translation
- Newline count match: `source.count('\n') == translation.count('\n')`
- Pipe-field count match: `source.count('||') + 1 == translation.count('||') + 1`
- unit_talk tag preservation: all `[unit_talk:XXX]` tags preserved

**If format_score == 0 → final_score = 0, verdict = REJECT**

### 2. term_consistency (weight: 0.25)
**Range**: 0.0–1.0

`term_consistency = active_terms_found_in_output / max(total_active_terms, 1)`

Where:
- `active_terms_found_in_output` = count of active terms whose glossary target appears in translation
- `total_active_terms` = count of active terms extracted from source

**Edge case**: If total_active_terms == 0, term_consistency = 1.0 (no terms to check)

### 3. fluency (weight: 0.25)
**Range**: 0.0–1.0

Heuristic checks:
- **Character ratio**: target/source character ratio within expected range for language pair (e.g., zh↔en: 0.4–0.8)
- **Repetition detection**: no character repeated > 10 times consecutively (garbled output)
- **Whitespace sanity**: reasonable whitespace patterns for target language
- **Target script presence**: sufficient ratio of characters from target language script

`fluency = average of above checks (each 0.0–1.0)`

### 4. completeness (weight: 0.25)
**Range**: 0.0–1.0

Heuristic checks:
- **Length ratio**: `len(translation) / max(len(source), 1)` within [0.3, 3.0] for most language pairs
- **Sentence/line count**: `count_sentences(translation) / max(count_sentences(source), 1)` within [0.5, 2.0]
- **Non-empty**: translation is not empty (unless source is empty)

`completeness = average of above checks (each 0.0–1.0)`

### 5. style_match (weight: 0.25)
**Range**: 0.0–1.0

Text-type-appropriate checks:
- **UI**: Short (< 50 chars typically), no sentence-ending punctuation for labels
- **Dialogue**: Contains conversational markers, quotes or dashes preserved
- **Skill**: Contains numbers/stats present, mechanical keywords intact
- **Quest**: Has both narrative flow and mechanical precision
- **System**: Formal tone, no casual language, consistent with system conventions

`style_match = type_appropriate_check(translation, text_type)`

## Composite Formula

```python
if format_score == 0:
    final_score = 0.0
    verdict = "REJECT"
else:
    final_score = (
        term_consistency * 0.25 +
        fluency * 0.25 +
        completeness * 0.25 +
        style_match * 0.25
    )
    
    if final_score >= PASS_SCORE_THRESHOLD:      # default 0.7
        verdict = "PASS"
    elif final_score >= REVIEW_SCORE_THRESHOLD:   # default 0.5
        verdict = "REVIEW"
    else:
        verdict = "REVIEW"  # elevated priority
```

## Thresholds

| Threshold | Default | Meaning |
|-----------|---------|---------|
| PASS_SCORE_THRESHOLD | 0.7 | Auto-accept if score >= 0.7 |
| REVIEW_SCORE_THRESHOLD | 0.5 | Send to reviewer if score < 0.7; < 0.5 is elevated priority |

## issue_tags Taxonomy

### Format issues (always trigger REJECT)
| Tag | Condition |
|-----|-----------|
| `fmt_placeholder` | Placeholder count or identity mismatch |
| `fmt_newline` | Newline count mismatch |
| `fmt_pipe` | Pipe-field count mismatch |
| `fmt_unit_talk` | unit_talk tag mismatch |

### Terminology issues
| Tag | Condition |
|-----|-----------|
| `term_miss:<term>` | Active term not found in translation |
| `term_wrong:<term>` | Term incorrectly translated vs glossary |
| `term_partial:<term>` | Only part of compound term found |

### Fluency issues
| Tag | Condition |
|-----|-----------|
| `fluency_repeat` | Suspicious character repetition detected |
| `fluency_garbled` | Character ratio out of expected range |
| `fluency_script` | Low target-script character presence |

### Completeness issues
| Tag | Condition |
|-----|-----------|
| `completeness_short` | Translation significantly shorter than expected |
| `completeness_long` | Translation significantly longer than expected |
| `completeness_truncated` | Translation appears cut off mid-sentence |

### Style issues
| Tag | Condition |
|-----|-----------|
| `style_mismatch` | Translation style doesn't match text_type expectations |
| `style_too_casual` | Casual language in formal/system context |
| `style_too_formal` | Overly formal in casual/dialogue context |

## AB Metrics Mapping

| Metric | Computation | Source |
|--------|------------|--------|
| success_rate | count(verdict==PASS) / total | Both A and B |
| format_break_rate | count(format_score==0) / total | Both A and B |
| term_consistency | average(term_consistency) | Both A and B |
| reviewer_trigger_rate | count(verdict==REVIEW) / total | B only |
| reviewer_improvement_rate | average((reviewed_score - draft_score) / draft_score) | B only (reviewed items) |

## Example Score Breakdowns

### Good translation (passes)
```
Source: "Fire Ball" (skill)
Translation: "火球术"
format_score: 1.0 (all placeholders/newlines/pipes intact)
term_consistency: 1.0 ("Fire Ball" -> "火球术" verified in glossary)
fluency: 0.9 (good zh ratio, no garbage)
completeness: 0.85 (zh shorter than en, expected)
style_match: 0.9 (skill-appropriate, concise)
final_score: 0.91 → PASS
```

### Bad translation (review)
```
Source: "Use {0} to defeat the {1}" (quest)
Translation: "用{0}打败" (truncated)
format_score: 1.0 (placeholders intact)
term_consistency: 0.5 (one term found, one missing)
fluency: 0.8 (acceptable)
completeness: 0.4 (too short, missing content)
style_match: 0.6 (partial quest structure)
final_score: 0.575 → REVIEW
issue_tags: [term_miss:defeat, completeness_short]
```

### Broken translation (reject)
```
Source: "Fire\nIce\nLightning" (UI)
Translation: "火焰冰霜闪电" (newlines lost!)
format_score: 0.0 (3 newlines expected, 0 found)
final_score: 0.0 → REJECT
issue_tags: [fmt_newline]
```
