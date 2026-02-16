#!/bin/bash
#
# Type check script for pi-mono-py
# Usage: ./scripts/typecheck.sh [--all|--staged|--src]
#

set -e

cd "$(dirname "$0")/.."

MODE="${1:---src}"

echo "🔍 Running type check (mode: $MODE)"
echo ""

case "$MODE" in
    --all)
        # Check all files including tests
        basedpyright packages/
        ;;
    --staged)
        # Check only staged files
        STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.py$' || true)
        if [ -z "$STAGED_FILES" ]; then
            echo "✅ No staged Python files to check"
            exit 0
        fi
        basedpyright $STAGED_FILES
        ;;
    --src|*)
        # Check only source files (exclude tests)
        basedpyright packages/pi_ai/src packages/pi_agent/src
        ;;
esac

echo ""
echo "✅ Type check passed"
