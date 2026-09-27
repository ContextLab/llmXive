"""
Run the initial git commit for the project.

This script orchestrates the git initialization process.
"""

import subprocess
import sys
from pathlib import Path

from code.git_operations import run_git_command
from code.init_git_repo import initialize_git_repository


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    # Determine project root (assume script is in code/ directory)
    current_path = Path(__file__).resolve()
    code_dir = current_path.parent
    project_root = code_dir.parent.parent

    print(f"Project root: {project_root}")

    # Initialize git repository
    if initialize_git_repository(project_root):
        print("Initial commit completed successfully.")
        return 0
    else:
        print("Failed to complete initial commit.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())