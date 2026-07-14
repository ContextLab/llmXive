"""
Script to initialize a Git repository for the project if not already initialized.
This ensures T001b is executable and verifiable.
"""
import os
import subprocess
import sys
from pathlib import Path

def initialize_git_repo():
    """Initialize git repository if .git does not exist."""
    project_root = Path(__file__).parent
    git_dir = project_root / ".git"

    if git_dir.exists():
        print(f"Git repository already initialized at {project_root}")
        return True

    try:
        # Initialize repository
        subprocess.run(
            ["git", "init"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Successfully initialized Git repository at {project_root}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to initialize Git repository: {e.stderr}")
        return False
    except FileNotFoundError:
        print("Error: 'git' command not found. Please install Git.")
        return False

if __name__ == "__main__":
    success = initialize_git_repo()
    sys.exit(0 if success else 1)