"""
Setup script for Git hooks in the llmXive project.
Creates pre-commit hooks to check for seeds and import conventions.
"""
import os
import stat
import sys
from pathlib import Path

from utils.logging import get_logger, log_provenance_event

logger = get_logger(__name__)

def setup_git_hooks():
    """
    Set up Git hooks for the project.
    
    Creates a pre-commit hook that:
    1. Checks for random seed initialization in Python files
    2. Validates import conventions
    """
    repo_root = Path(__file__).parent.parent
    git_hooks_dir = repo_root / '.git' / 'hooks'
    code_dir = repo_root / 'code'
    
    # Ensure .git/hooks directory exists
    if not git_hooks_dir.exists():
        logger.warning("Not a Git repository. Skipping hook setup.")
        return False
    
    # Create hook scripts directory in code/
    hook_scripts_dir = code_dir / 'hook_scripts'
    hook_scripts_dir.mkdir(exist_ok=True)
    
    # Path to pre-commit hook
    pre_commit_hook = git_hooks_dir / 'pre-commit'
    
    # Create the pre-commit hook script
    hook_content = f'''#!/bin/bash
    # Pre-commit hook for llmXive project
    # Checks for seed initialization and import conventions
    
    set -e
    
    echo "Running pre-commit checks..."
    
    # Run seed check
    python3 "{code_dir}/hook_scripts/check_seeds.py"
    SEED_EXIT=$?
    
    # Run import check
    python3 "{code_dir}/hook_scripts/check_imports.py"
    IMPORT_EXIT=$?
    
    if [ $SEED_EXIT -ne 0 ] || [ $IMPORT_EXIT -ne 0 ]; then
        echo ""
        echo "⚠️  Pre-commit checks completed with warnings."
        echo "Please review the output above before committing."
        # Don't block the commit, just warn
    else
        echo "✅ All pre-commit checks passed."
    fi
    
    exit 0
    '''
    
    # Write the pre-commit hook
    try:
        with open(pre_commit_hook, 'w', encoding='utf-8') as f:
            f.write(hook_content)
        
        # Make it executable
        os.chmod(pre_commit_hook, os.stat(pre_commit_hook).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        
        logger.info(f"Pre-commit hook created at {pre_commit_hook}")
        log_provenance_event("git_hook_setup", {
            "hook_type": "pre-commit",
            "checks": ["seed_initialization", "import_conventions"],
            "status": "success"
        })
        
        return True
    except Exception as e:
        logger.error(f"Failed to create pre-commit hook: {str(e)}")
        return False

def main():
    """Main entry point for the setup script."""
    logger.info("Setting up Git hooks...")
    
    success = setup_git_hooks()
    
    if success:
        logger.info("Git hooks setup completed successfully.")
        print("✅ Git hooks have been set up.")
        print("   The pre-commit hook will check for:")
        print("   - Random seed initialization")
        print("   - Import conventions")
    else:
        logger.warning("Git hooks setup failed or was skipped.")
        print("⚠️  Git hooks setup failed or was skipped.")
        print("   You may need to manually set up hooks if not in a Git repository.")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())