---
name: implement-v35
description: "Implement V3.5 behind flags in translate_multi_language.py, and add quality logging."
argument-hint: "[scope chunk: classifier|prompt_router|glossary|scorer|reviewer|logging|qa]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash
---

# /implement-v35

Implement one chunk of the V3.5 enhancement into the translation script.

## Input
- Read `CLAUDE.md` for non-negotiables and feature flags
- Read `src/translate_multi_language.py`
- Read relevant `.claude/docs/` design document (prompts.md / glossary.md / scoring.md)
- Optional argument: scope chunk to implement

## Process (for each chunk)
1. Read the current state of `src/translate_multi_language.py`
2. Identify insertion points (minimal, near related existing logic)
3. Add new function(s) behind feature flag
4. Add config flag entry
5. Wire into translate() pipeline
6. Run `bash .claude/hooks/validate-structure.sh`
7. Append to `production/change_log.md`

## Implementation Rules
- Add functions, do not rewrite existing ones
- Every new code path: `if CONFIG.get("FLAG", False): try... except: fallback`
- On classification failure: fallback to text_type="normal"
- On scorer failure: skip scoring, log warning
- On reviewer failure: use draft as-is
- Any change touching structure protection MUST update `tests/acceptance_check.py`

## Output Contract
- Modify `src/translate_multi_language.py`
- Append entry to `production/change_log.md` with: timestamp, scope, summary, flag added
- Run `bash .claude/hooks/validate-structure.sh` and report results
