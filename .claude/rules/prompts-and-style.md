---
paths:
  - "src/translate_multi_language.py"
  - ".claude/docs/prompts.md"
---

# Prompts and Style Rules

## Prompt Template Rules
- Adding or modifying prompt templates MUST sync to `.claude/docs/prompts.md`
- Every prompt MUST contain: "Output only the translation, no explanations or alternatives"
- Every prompt MUST include placeholder protection instruction
- Every prompt MUST include newline preservation instruction

## Style Rules
- Text type classification determines which prompt template to use
- If classifier fails or is disabled, use the `normal` prompt template
- Reviewer prompt MUST instruct: "Fix only the identified issues; do not change correct parts"

## Review Gate
- Prompt changes require re-running smoke-10 to verify no regressions
