"""
Task T004: Initialize Git Repository.

Action: Run `git init` in the project root.
Verification: `.git` directory exists.

This script is designed to be run as:
`python scripts/init_git_repo.py`
"""
import os
import subprocess
import sys
from pathlib import Path

def main():
    # Determine the project root.
    # Based on the execution context, the script is located at code/scripts/
    # The project root is the parent of 'code'.
    script_path = Path(__file__).resolve()
    current_dir = script_path.parent
    project_root = current_dir.parent

    git_dir = project_root / ".git"

    if git_dir.exists():
        print(f"Git repository already initialized at: {project_root}")
        return 0

    print(f"Initializing Git repository at: {project_root}")
    try:
        # Run git init
        result = subprocess.run(
            ["git", "init"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Git init output: {result.stdout}")
        if result.stderr:
            print(f"Git init stderr: {result.stderr}")
        
        if not git_dir.exists():
            print("ERROR: .git directory was not created after 'git init'.")
            return 1
        
        print("Git repository successfully initialized.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to initialize git repository: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return 1
    except FileNotFoundError:
        print("ERROR: 'git' command not found. Please ensure git is installed and in PATH.")
        return 1

if __name__ == "__main__":
    sys.exit(main())