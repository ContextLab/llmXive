"""
Task T004: Initialize Git Repository.
Action: Run `git init` in the project root.
Verification: `.git` directory exists.
"""
import os
import subprocess
import sys
from pathlib import Path

def main():
    """Initialize a git repository in the current directory."""
    # Determine the project root (assuming script is in scripts/)
    # We run git init in the parent directory of the scripts folder
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    print(f"Initializing git repository at: {project_root}")

    try:
        # Run git init
        result = subprocess.run(
            ["git", "init"],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Error initializing git repository: {result.stderr}")
            sys.exit(1)

        print("Git repository initialized successfully.")
        print(result.stdout)

        # Verify .git directory exists
        git_dir = project_root / ".git"
        if git_dir.exists() and git_dir.is_dir():
            print(f"Verification successful: .git directory exists at {git_dir}")
        else:
            print("Error: .git directory was not created.")
            sys.exit(1)

    except FileNotFoundError:
        print("Error: 'git' command not found. Please ensure git is installed and in PATH.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()