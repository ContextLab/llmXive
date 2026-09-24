import os
import subprocess
import sys
from pathlib import Path
from code.git_operations import init_repository, stage_all_files, commit_changes

def initialize_git_repository(project_root: Path) -> bool:
    """
    Initialize the git repository, stage all files, and make the initial commit.
    """
    print(f"Initializing git repository at: {project_root}")

    # Initialize
    stdout, stderr, code = init_repository(project_root)
    if code != 0:
        print(f"Error initializing git: {stderr}")
        return False
    print("Git repository initialized.")

    # Stage all files
    stdout, stderr, code = stage_all_files(project_root)
    if code != 0:
        print(f"Error staging files: {stderr}")
        return False
    print("Files staged.")

    # Commit
    stdout, stderr, code = commit_changes(project_root, "Initial commit")
    if code != 0:
        print(f"Error committing: {stderr}")
        return False
    print("Initial commit created.")

    return True

def main():
    project_root = Path(__file__).resolve().parent.parent
    success = initialize_git_repository(project_root)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
