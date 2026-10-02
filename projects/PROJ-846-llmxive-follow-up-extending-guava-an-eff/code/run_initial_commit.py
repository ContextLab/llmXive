import subprocess
import sys
from pathlib import Path
from code.git_operations import run_git_command
from code.init_git_repo import initialize_git_repository

def main():
    """
    Orchestrates the git initialization process.
    This script is designed to be run as the first step in project setup.
    """
    root_path = Path.cwd()
    print(f"Running initial commit setup for project at: {root_path}")

    # Check if git is already initialized
    try:
        run_git_command(['git', 'rev-parse', '--git-dir'], cwd=root_path)
        print("Git repository already initialized.")
        # Optionally, we could skip or force re-initialization
        # For now, we assume the user wants to ensure a clean state
        # but we won't destroy existing history.
        return 0
    except subprocess.CalledProcessError:
        pass  # Not initialized, proceed

    success = initialize_git_repository(root_path)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
