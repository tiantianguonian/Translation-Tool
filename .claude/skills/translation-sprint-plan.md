---
name: translation-sprint-plan
description: "Create a 1-week incremental plan for V3.5 with deliverables and risk controls."
argument-hint: "[optional focus: classifier|prompts|glossary|scoring|reviewer|qa|ops]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit
---

# /translation-sprint-plan

Create a 1-week incremental implementation plan for the V3.5 translation enhancement.

## Input
- Read `CLAUDE.md` for non-negotiables, feature flags, and DoD
- Read `production/session-state/active.md` for current state
- Read `production/todo.md` for outstanding items

## Process
1. Assess current state from active.md and CLAUDE.md
2. Decompose remaining work into modules with clear dependencies
3. Prioritize by risk (low-risk first, high-risk gated)
4. Assign each module a feature flag and owner agent
5. Define per-module acceptance criteria
6. Estimate effort per module (rounds of Claude Code interaction)

## Output Contract
- Write `production/sprints/sprint-v35-week1.md` with sections:
  - scope / constraints / modules / execution_order / deliverables / acceptance_criteria
- Update `production/todo.md` with new items
- Update `production/session-state/active.md` with sprint plan reference
