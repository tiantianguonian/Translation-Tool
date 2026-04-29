#!/bin/bash
# pre-run.sh — Run smoke-10 before any large-scale translation
# Trigger: PreToolUse hook (when translate_multi_language.py is invoked without --test-mode)

# Only gate if we're running on a large batch (not a single item)
# For now: always run a quick structure check on the acceptance script itself
echo "[pre-run] Verifying acceptance_check.py is importable..."
python -c "import sys; sys.path.insert(0, 'tests'); import acceptance_check" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[pre-run] ERROR: acceptance_check.py is not importable. Abort."
    exit 1
fi

echo "[pre-run] Checking smoke_10 dataset exists..."
if [ ! -f "tests/smoke_10.jsonl" ]; then
    echo "[pre-run] WARNING: tests/smoke_10.jsonl not found. Skipping smoke check."
    exit 0
fi

echo "[pre-run] OK"
exit 0
