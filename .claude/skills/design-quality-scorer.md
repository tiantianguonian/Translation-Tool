---
name: design-quality-scorer
description: "Define scoring dimensions, formula, thresholds, issue tags, and AB metrics mapping."
user-invocable: true
allowed-tools: Read, Write, Edit
---

# /design-quality-scorer

Design the 5-dimension heuristic quality scoring system.

## Input
- Read `CLAUDE.md` for PASS_SCORE_THRESHOLD, REVIEW_SCORE_THRESHOLD
- Read `.claude/docs/glossary.md` for term-related scoring inputs

## Process
1. Define 5 scoring dimensions with weights:
   - format_score (HARD GATE, binary 0/1)
   - term_consistency (0.25)
   - fluency (0.25)
   - completeness (0.25)
   - style_match (0.25)
2. Define heuristic check for each dimension
3. Define composite formula with format_score as gate
4. Set PASS/REVIEW/REJECT thresholds
5. Define issue_tags taxonomy (fmt_*, term_*, fluency_*, completeness_*, style_*)
6. Map scoring output to AB metrics

## Output Contract
- Write to `.claude/docs/scoring.md`
- Include formula, thresholds, issue_tags taxonomy, AB metrics mapping
- Include examples: score breakdown for a good translation and a bad one
