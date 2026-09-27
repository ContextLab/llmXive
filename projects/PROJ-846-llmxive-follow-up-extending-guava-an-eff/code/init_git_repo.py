"""
Initialize Git Repository for llmXive project.

This script creates a .gitignore file, initializes a git repository,
stages all files, and creates an initial commit.
"""

import os
import subprocess
import sys
from pathlib import Path

from code.git_operations import init_repository, stage_all_files, commit_changes


def initialize_git_repository(project_root: Path) -> bool:
    """
    Initialize the git repository for the project.

    Args:
        project_root: Path to the project root directory.

    Returns:
        True if initialization was successful, False otherwise.
    """
    try:
        # Change to project root
        os.chdir(project_root)

        # Initialize git repository
        init_repository()

        # Stage all files
        stage_all_files()

        # Commit changes
        commit_changes("Initial commit")

        return True
    except subprocess.CalledProcessError as e:
        print(f"Git operation failed: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error during git initialization: {e}", file=sys.stderr)
        return False


def main() -> int:
    """
    Main entry point for the script.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    # Determine project root (assume script is in code/ directory)
    current_path = Path(__file__).resolve()
    code_dir = current_path.parent
    project_root = code_dir.parent.parent

    print(f"Project root: {project_root}")
    print("Initializing Git Repository...")

    if initialize_git_repository(project_root):
        print("Git repository initialized successfully.")
        return 0
    else:
        print("Failed to initialize Git repository.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
