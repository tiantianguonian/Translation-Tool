#!/bin/bash
# validate-jsonl.sh — Validate quality log JSONL integrity
# Usage: bash .claude/hooks/validate-jsonl.sh <path/to/file.jsonl>

JSONL_FILE="${1:-production/quality_logs/smoke_10.jsonl}"

if [ ! -f "$JSONL_FILE" ]; then
    echo "[validate-jsonl] ERROR: File not found: $JSONL_FILE"
    exit 1
fi

REQUIRED_FIELDS="timestamp sample_id text_type format_score term_consistency fluency completeness style_match final_score verdict"

LINE_NUM=0
ERRORS=0
while IFS= read -r line; do
    LINE_NUM=$((LINE_NUM + 1))

    # Skip empty lines
    [ -z "$line" ] && continue

    # Check valid JSON
    echo "$line" | python -c "import json,sys; json.loads(sys.stdin.read())" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "[validate-jsonl] ERROR: Line $LINE_NUM is not valid JSON"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    # Check required fields
    for field in $REQUIRED_FIELDS; do
        has_field=$(echo "$line" | python -c "import json,sys; d=json.loads(sys.stdin.read()); print(1 if '$field' in d else 0)" 2>/dev/null)
        if [ "$has_field" = "0" ]; then
            echo "[validate-jsonl] ERROR: Line $LINE_NUM missing required field: $field"
            ERRORS=$((ERRORS + 1))
        fi
    done
done < "$JSONL_FILE"

if [ $ERRORS -eq 0 ]; then
    echo "[validate-jsonl] OK: $JSONL_FILE ($LINE_NUM lines, 0 errors)"
    exit 0
else
    echo "[validate-jsonl] FAIL: $JSONL_FILE ($LINE_NUM lines, $ERRORS errors)"
    exit 1
fi
