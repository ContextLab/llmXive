"""
Script to install Git pre-commit hooks for the project.
Sets up hooks for seed verification and import consistency checks.
"""
import os
import stat
import sys
from pathlib import Path


def setup_git_hooks():
    """Install pre-commit hooks into the .git/hooks directory."""
    repo_root = Path(__file__).parent
    git_hooks_dir = repo_root / ".git" / "hooks"
    pre_commit_hook = git_hooks_dir / "pre-commit"

    # Create .git/hooks directory if it doesn't exist
    git_hooks_dir.mkdir(parents=True, exist_ok=True)

    # Content for the pre-commit hook
    hook_content = """#!/bin/bash
    # Pre-commit hook for seed verification and import consistency

    echo "Running pre-commit checks..."

    # Run seed verification
    echo "Checking random seeds..."
    python code/utils/verify_seed.py
    if [ $? -ne 0 ]; then
        echo "❌ Seed verification failed. Please fix the issues above."
        exit 1
    fi

    # Run import consistency check
    echo "Checking import consistency..."
    python code/utils/check_imports.py
    if [ $? -ne 0 ]; then
        echo "❌ Import consistency check failed. Please fix the issues above."
        exit 1
    fi

    # Run pre-commit framework (if installed)
    if command -v pre-commit &> /dev/null; then
        echo "Running pre-commit framework..."
        pre-commit run
        if [ $? -ne 0 ]; then
            echo "❌ Pre-commit framework checks failed."
            exit 1
        fi
    fi

    echo "✅ All pre-commit checks passed."
    exit 0
    """

    # Write the hook file
    pre_commit_hook.write_text(hook_content)

    # Make the hook executable
    pre_commit_hook.chmod(pre_commit_hook.stat().st_mode | stat.S_IEXEC)

    print(f"✅ Pre-commit hook installed at {pre_commit_hook}")

    # Also install pre-commit framework configuration
    pre_commit_config = repo_root / ".pre-commit-config.yaml"
    if pre_commit_config.exists():
        print("✅ Pre-commit configuration file found.")
        print("   Run 'pre-commit install' to use the pre-commit framework.")
    else:
        print("⚠️  No .pre-commit-config.yaml found. Creating one...")
        # Create a basic config
        config_content = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]
"""
        pre_commit_config.write_text(config_content)
        print(f"✅ Created {pre_commit_config}")

    return 0


def main():
    """Main entry point for the script."""
    print("🔧 Setting up Git hooks...")
    return setup_git_hooks()


if __name__ == "__main__":
    sys.exit(main())