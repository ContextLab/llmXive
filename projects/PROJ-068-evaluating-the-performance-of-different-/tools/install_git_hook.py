#!/usr/bin/env python3
"""
Script to install the pre-commit checksum hook.

This script creates a symbolic link from .git/hooks/pre-commit to
tools/pre-commit-checksum.py.

Usage:
    python tools/install_git_hook.py
"""
import os
import sys
from pathlib import Path
import stat

PROJECT_ROOT = Path(__file__).parent.parent
GIT_HOOKS_DIR = PROJECT_ROOT / ".git" / "hooks"
PRE_COMMIT_SCRIPT = PROJECT_ROOT / "tools" / "pre-commit-checksum.py"
HOOK_LINK = GIT_HOOKS_DIR / "pre-commit"

def main() -> int:
    """Install the pre-commit hook."""
    print("Installing pre-commit checksum hook...")
    
    # Check if .git directory exists
    git_dir = PROJECT_ROOT / ".git"
    if not git_dir.exists():
        print("❌ Error: Not a git repository. Please initialize git first with 'git init'.")
        return 1
    
    # Create .git/hooks directory if it doesn't exist
    GIT_HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if pre-commit script exists
    if not PRE_COMMIT_SCRIPT.exists():
        print(f"❌ Error: Pre-commit script not found at {PRE_COMMIT_SCRIPT}")
        return 1
    
    # Remove existing hook if it exists
    if HOOK_LINK.exists() or HOOK_LINK.is_symlink():
        print(f"Removing existing hook at {HOOK_LINK}")
        HOOK_LINK.unlink()
    
    # Create symbolic link
    try:
        # Use relative path for the symlink
        relative_path = os.path.relpath(PRE_COMMIT_SCRIPT, GIT_HOOKS_DIR)
        HOOK_LINK.symlink_to(relative_path)
        print(f"✅ Created symbolic link: {HOOK_LINK} -> {relative_path}")
    except Exception as e:
        print(f"❌ Error creating symbolic link: {e}")
        return 1
    
    # Make the hook executable
    try:
        HOOK_LINK.chmod(HOOK_LINK.stat().st_mode | stat.S_IEXEC)
        print("✅ Made hook executable")
    except Exception as e:
        print(f"⚠️ Warning: Could not make hook executable: {e}")
    
    print("\n✅ Pre-commit hook installed successfully.")
    print("The hook will now run before each commit to verify data integrity.")
    return 0

if __name__ == "__main__":
    sys.exit(main())