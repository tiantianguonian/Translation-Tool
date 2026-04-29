---
paths:
  - "src/translate_multi_language.py"
---

# Translation Core Safety Rules

## Non-negotiables
- Any change touching placeholder/newline/pipe-field logic MUST update tests/acceptance_check.py
- Any change touching unit_talk parsing MUST add at least one smoke sample covering unit_talk

## Review Gate
- format_score must be a hard gate: if broken, translation is rejected regardless of other scores
- Any format_score == 0 result in smoke-10 is a BLOCK issue

## Structure Invariants
- Placeholder count and identity must be preserved: `{0}`, `%s`, `{name}` etc.
- Newline count must be preserved: `\n`, `\r\n`
- Pipe-field count and order must be preserved: `||`
- unit_talk tags must be preserved exactly

## Feature Flag Rules
- Every new code path must be gated behind a feature flag
- Default value for all feature flags is False (opt-in)
- Feature flag names must match those declared in CLAUDE.md
