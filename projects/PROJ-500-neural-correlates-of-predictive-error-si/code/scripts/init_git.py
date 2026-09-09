"""
Script to initialize the Git repository for the project.
This script must be run before any other git operations.
"""
import os
import subprocess
import sys
from pathlib import Path


def initialize_git_repository(project_root: Path) -> bool:
    """
    Initialize a Git repository in the specified project root.

    Args:
        project_root: Path to the project root directory.

    Returns:
        True if initialization was successful, False otherwise.
    """
    if not project_root.exists():
        print(f"Error: Project root directory does not exist: {project_root}")
        return False

    # Change to the project root directory
    os.chdir(project_root)

    try:
        # Run git init command
        result = subprocess.run(
            ["git", "init"],
            capture_output=True,
            text=True,
            check=True
        )
        print("Git repository initialized successfully.")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error initializing Git repository: {e.stderr}")
        return False
    except FileNotFoundError:
        print("Error: Git is not installed or not found in PATH.")
        return False


def main():
    """Main entry point for the script."""
    # Determine the project root (assuming script is in code/scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    print(f"Initializing Git repository in: {project_root}")

    success = initialize_git_repository(project_root)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
