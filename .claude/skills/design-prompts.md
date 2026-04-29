---
name: design-prompts
description: "Generate typed prompt templates + reviewer prompt, with strict formatting rules."
argument-hint: "[target language + constraints]"
user-invocable: true
allowed-tools: Read, Write, Edit
---

# /design-prompts

Generate the typed prompt templates for game localization across 5 text types.

## Input
- Read `CLAUDE.md` for non-negotiables (placeholder, newline, pipe, unit_talk protection)
- Optional: target language, additional constraints

## Process
1. Design system prompt preamble (translator role, constraints, output format)
2. For each text type (UI, Dialogue, Skill, Quest, System):
   - Define type-specific instructions (tone, length, terminology priority)
   - Include placeholder/newline/pipe/unit_talk protection instruction
   - Add "Output only the translation" constraint
3. Design reviewer prompt template:
   - Receives source + draft + scores + issue_tags
   - Instructs to fix only identified issues

## Output Contract
- Write to `.claude/docs/prompts.md`
- Each prompt must be a complete, ready-to-use template
- Each prompt must have a unique identifier (e.g., `## prompt_ui`)
- Include a `## reviewer_prompt` section
