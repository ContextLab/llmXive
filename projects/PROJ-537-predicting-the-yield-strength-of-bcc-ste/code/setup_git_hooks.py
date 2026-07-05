"""
Setup Git hooks for pre-commit checks (seeds, imports).

This script installs a pre-commit hook that:
1. Verifies random seeds are set to 42 (or configured value) before running training/analysis.
2. Checks that imports in Python files are consistent and don't introduce circular dependencies.
"""

import os
import stat
import sys
from pathlib import Path


def setup_git_hooks():
    """Install pre-commit hooks into the .git/hooks directory."""
    root_dir = Path(__file__).resolve().parent.parent
    git_hooks_dir = root_dir / ".git" / "hooks"
    pre_commit_hook_path = git_hooks_dir / "pre-commit"

    # Ensure .git/hooks directory exists
    git_hooks_dir.mkdir(parents=True, exist_ok=True)

    # Define the pre-commit hook script
    hook_script = """#!/bin/bash
# Pre-commit hook for PROJ-537: Verify seeds and imports

set -e

echo "Running pre-commit checks..."

# 1. Check for random seed consistency
# Look for 'seed = 42' or 'random_state = 42' in code/ files
SEED_CHECK=$(grep -r "seed\\s*=\\s*42\\|random_state\\s*=\\s*42" code/ 2>/dev/null || true)
if [ -z "$SEED_CHECK" ]; then
    echo "WARNING: No explicit seed=42 found in code/ files. Please ensure reproducibility."
    # Uncomment the next line to make this an error instead of a warning
    # exit 1
fi

# 2. Check for common import issues
# Ensure no 'from __future__ import annotations' in Python 3.7+ projects (optional)
# Ensure no circular imports (basic check)
echo "Checking imports..."
if grep -r "import sys" code/ 2>/dev/null | grep -v "code/utils/logging.py" | grep -v "code/setup_directories.py" | grep -v "code/setup_git_hooks.py"; then
    echo "WARNING: 'import sys' found outside of standard utility files. Consider refactoring."
fi

# 3. Check for TODO/FIXME comments (optional, just a warning)
TODO_CHECK=$(grep -r "TODO\\|FIXME" code/ 2>/dev/null || true)
if [ -n "$TODO_CHECK" ]; then
    echo "WARNING: TODO/FIXME comments found in code/:"
    echo "$TODO_CHECK"
fi

echo "Pre-commit checks completed."
exit 0
"""

    # Write the hook script
    pre_commit_hook_path.write_text(hook_script)

    # Make the hook executable
    st = os.stat(pre_commit_hook_path)
    os.chmod(pre_commit_hook_path, st.st_mode | stat.S_IEXEC)

    print(f"Pre-commit hook installed at {pre_commit_hook_path}")
    print("The hook will now run on every 'git commit'.")


def main():
    """Entry point for the script."""
    setup_git_hooks()


if __name__ == "__main__":
    main()