---
name: design-glossary-activation
description: "Define active-term extraction and deterministic term validation, plus term issue tags."
user-invocable: true
allowed-tools: Read, Write, Edit
---

# /design-glossary-activation

Design the glossary system: active-term extraction, post-translation validation, and term issue tags.

## Input
- Read `CLAUDE.md` for feature flags (ENABLE_TERM_CHECK, ACTIVE_TERMS_LIMIT)
- Read game glossary if available (CSV/JSON of source→target term mappings)

## Process
1. Define glossary data format (CSV with columns: source_term, target_term, text_type, priority)
2. Design `extract_active_terms(source_text, glossary, limit)` algorithm:
   - Longest-match first
   - Punctuation boundary handling (CJK + Latin)
   - Non-overlapping selection
   - Truncation to ACTIVE_TERMS_LIMIT
3. Design post-translation validation:
   - Check each active term's target appears in translation
   - Define acceptable variations per target language
4. Define term-related issue_tags

## Output Contract
- Write to `.claude/docs/glossary.md`
- Include pseudocode for `extract_active_terms()`
- Include example: input text → active terms → validation result
