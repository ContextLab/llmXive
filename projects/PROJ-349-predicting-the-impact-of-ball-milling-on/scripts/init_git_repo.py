import os
import subprocess
import sys
from pathlib import Path

def main():
    """
    Initialize a Git repository in the project root.
    Verification: .git directory exists after execution.
    """
    project_root = Path(__file__).resolve().parent.parent
    git_dir = project_root / ".git"

    if git_dir.exists():
        print(f"Git repository already initialized at {git_dir}")
        return 0

    try:
        print(f"Initializing Git repository at {project_root}...")
        subprocess.run(
            ["git", "init"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True
        )
        print("Git repository initialized successfully.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Failed to initialize Git repository: {e.stderr}")
        return 1
    except FileNotFoundError:
        print("Error: 'git' command not found. Please install Git.")
        return 1

if __name__ == "__main__":
    sys.exit(main())