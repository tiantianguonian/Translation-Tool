#!/bin/bash
# session-start.sh — Print current branch, recent experiments, and active.md summary
# Trigger: SessionStart hook in .claude/settings.json

echo "=== V3.5 Session Start ==="
echo ""

# Current git branch (if in a repo)
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Branch: $(git branch --show-current 2>/dev/null || echo 'detached')"
    echo "Last commit: $(git log -1 --format='%h %s' 2>/dev/null || echo 'none')"
else
    echo "Branch: N/A (not a git repository)"
fi

echo ""

# Active state summary
if [ -f "production/session-state/active.md" ]; then
    echo "--- Active State ---"
    head -12 production/session-state/active.md
else
    echo "WARNING: production/session-state/active.md not found"
fi

echo ""

# Recent experiments
if [ -d "production/experiments" ]; then
    echo "--- Recent Experiments ---"
    ls -1 production/experiments/ 2>/dev/null | head -5 || echo "  (none)"
fi

echo ""

# Recent change log tail
if [ -f "production/change_log.md" ]; then
    echo "--- Recent Changes ---"
    tail -8 production/change_log.md
fi

echo ""
echo "=== Ready ==="
