#!/bin/bash
# validate-structure.sh — Validate placeholder/newline/||/unit_talk structure safety
# Usage: bash .claude/hooks/validate-structure.sh

echo "[validate-structure] Running structure safety checks..."

# Run the acceptance check script
if [ -f "tests/acceptance_check.py" ]; then
    python tests/acceptance_check.py 2>&1
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo "[validate-structure] OK: All structure safety checks passed"
        exit 0
    else
        echo "[validate-structure] FAIL: Structure safety checks failed (exit code: $EXIT_CODE)"
        exit 1
    fi
else
    echo "[validate-structure] WARNING: tests/acceptance_check.py not found. Skipping."
    exit 0
fi
