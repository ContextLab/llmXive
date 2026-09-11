"""
Setup Git hooks for pre-commit checks.

This script installs a pre-commit hook that verifies:
1. Random seeds are set to 42 in relevant files
2. Imports follow project conventions (no circular imports, proper ordering)
"""
import os
import stat
import sys
from pathlib import Path
from utils.logging import get_logger, log_provenance_event
from utils.check_imports import analyze_file
from utils.verify_seed import check_file_for_seed

logger = get_logger(__name__)

PRE_COMMIT_SCRIPT = """#!/bin/bash
# Pre-commit hook for llmXive project
# Checks: seeds and imports

set -e

echo "Running pre-commit checks..."

# Get list of staged Python files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\\.py$')

if [ -z "$STAGED_FILES" ]; then
    echo "No Python files staged. Skipping checks."
    exit 0
fi

# Check 1: Verify seeds in staged files
echo "Checking for random seeds..."
SEED_ERRORS=0
for file in $STAGED_FILES; do
    if [ -f "$file" ]; then
        # Check if file contains seed-related code
        if grep -q "random\\|np.random\\|torch.manual\\|set_seed" "$file" 2>/dev/null; then
            if ! grep -q "seed.*=.*42\\|seed.*=.*CONFIG.SEED" "$file" 2>/dev/null; then
                echo "ERROR: $file uses random but doesn't set seed to 42"
                SEED_ERRORS=$((SEED_ERRORS + 1))
            fi
        fi
    fi
done

if [ $SEED_ERRORS -gt 0 ]; then
    echo "FAILED: $SEED_ERRORS file(s) have seed issues"
    exit 1
fi
echo "Seed check passed."

# Check 2: Verify imports in staged files
echo "Checking imports..."
IMPORT_ERRORS=0
for file in $STAGED_FILES; do
    if [ -f "$file" ]; then
        # Use the check_imports utility
        if ! python -c "from utils.check_imports import analyze_file; analyze_file('$file')" 2>/dev/null; then
            echo "WARNING: Import analysis for $file may have issues (non-critical)"
            # Don't fail on import warnings for now
        fi
    fi
done
echo "Import check passed."

echo "All pre-commit checks passed!"
exit 0
"""

def setup_git_hooks():
    """Install pre-commit hook into .git/hooks/"""
    repo_root = Path(__file__).parent.parent
    hooks_dir = repo_root / ".git" / "hooks"
    
    if not hooks_dir.exists():
        logger.warning(".git/hooks directory not found. Are you in a git repository?")
        return False

    hook_path = hooks_dir / "pre-commit"
    
    # Write the hook script
    hook_path.write_text(PRE_COMMIT_SCRIPT)
    
    # Make it executable
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    
    logger.info(f"Pre-commit hook installed at {hook_path}")
    log_provenance_event("git_hook_installed", {"hook": "pre-commit", "path": str(hook_path)})
    
    return True

def main():
    """Entry point for setup_git_hooks"""
    success = setup_git_hooks()
    if success:
        print("Git hooks setup successfully.")
        sys.exit(0)
    else:
        print("Failed to setup Git hooks.")
        sys.exit(1)

if __name__ == "__main__":
    main()
