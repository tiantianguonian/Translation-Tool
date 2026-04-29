# Glossary — Game Translation V3.5

> Design document for active-term extraction and deterministic terminology validation.

## Glossary Data Format

Glossary entries stored as CSV with columns:
```
source_term,target_term,text_type,priority
```

- `source_term`: term in source language (e.g., "Fire Ball")
- `target_term`: official translation in target language (e.g., "火球术")
- `text_type`: which text types this term applies to (UI|dialogue|skill|quest|system|*)
- `priority`: 1 (critical/system) to 5 (flavor/lore), lower = higher priority

## extract_active_terms(source_text, glossary, limit=20)

### Algorithm (Longest-Match First)

```
function extract_active_terms(source_text, glossary, limit):
    matches = []
    text_lower = source_text.lower()
    
    for each term in glossary:
        term_lower = term.source_term.lower()
        # Find all occurrences
        positions = find_all(text_lower, term_lower)
        for each pos in positions:
            if is_word_boundary(text_lower, pos, len(term_lower)):
                matches.append({
                    term: term,
                    position: pos,
                    length: len(term.source_term)
                })
    
    # Sort: longest first, then earliest position
    sort(matches, key=(length desc, position asc))
    
    # Remove overlaps: keep longest, skip overlapped
    selected = []
    occupied_ranges = []
    for match in matches:
        if not overlaps(match, occupied_ranges):
            selected.append(match.term)
            occupied_ranges.append(match.range)
    
    # Truncate to limit, sorted by priority then length
    sort(selected, key=(priority asc, length desc))
    return selected[:limit]
```

### Word Boundary Rules

**Latin text**: Term must start and end on a word boundary (space, punctuation, start/end of string).
- "fire" matches "cast fire ball" but NOT "fireball"
- "fire" does NOT match "fire, and ice"

**CJK text**: Term can match on character boundaries without spaces.
- "火球" matches "使用火球术攻击" (no spaces needed)
- "火球" does NOT match "冰火球" (character boundary: "冰"+"火球" is valid only if "火球" starts at position 1)

### Punctuation Boundary Characters
```
Latin: space . , ! ? ; : " ' ( ) [ ] { } - — / \ | @ # $ % ^ & * + = ~ ` < >
CJK:  。 ， ！ ？ ； ： " " ' ' （ ） 【 】 《 》 、 … — ～
```

## Post-Translation Term Validation

For each active term that was extracted from the source:
1. Get the expected target_term from glossary
2. Check if target_term appears in the translated output
3. If NOT found: add `term_miss:<source_term>` to issue_tags
4. If found but in a different form (partial match): add `term_partial:<source_term>`

### Acceptable Variations (target-language specific)
- **zh-cn/zh-tw**: Allow 的/之/地/得 particle variations
- **ja**: Allow okurigana variations for kanji terms
- **ko**: Allow particle suffix variations (은/는/이/가/을/를)
- **Latin languages**: Allow plural/singular, gender agreement variations

## Issue Tags for Glossary

| Tag | Meaning |
|-----|---------|
| `term_miss:fire_ball` | Active term "fire_ball" not found in translation at all |
| `term_wrong:fire_ball` | Term translated but doesn't match glossary target |
| `term_partial:fire_ball` | Only part of a compound term matched |

## ACTIVE_TERMS_LIMIT Truncation

When more terms match than ACTIVE_TERMS_LIMIT:
1. Sort by priority (lower number = higher priority)
2. Within same priority, sort by match length (longest first)
3. Truncate to ACTIVE_TERMS_LIMIT
4. Log truncated terms at DEBUG level

## Example

**Input**: "Use Fire Ball to attack the Ice Golem in Frozen Cave"
**Glossary**: [Fire Ball→火球术, Ice Golem→冰魔像, Frozen Cave→冰窟, Fire→火焰, Ice→冰]
**Active terms** (longest-match, no overlap):
1. "Fire Ball" (len 9, pos 4) ✓ selected
2. "Frozen Cave" (len 11, pos 38) ✓ selected  
3. "Ice Golem" (len 9, pos 26) ✓ selected
4. "Fire" (len 4, pos 4) ✗ overlaps with "Fire Ball"
5. "Ice" (len 3, pos 26) ✗ overlaps with "Ice Golem"

**Result**: ["Fire Ball", "Frozen Cave", "Ice Golem"]
