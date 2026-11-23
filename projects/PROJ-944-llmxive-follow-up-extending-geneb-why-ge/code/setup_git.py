"""
Initialize git repository for the project.
This script creates a .git directory if one does not exist.
"""
import os
import subprocess
from pathlib import Path

def main():
    """Initialize git repo if not already initialized."""
    root = Path(__file__).resolve().parent.parent
    git_dir = root / ".git"

    if git_dir.exists():
        print("Git repository already initialized.")
        return

    print("Initializing git repository...")
    try:
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
        print("Git repository initialized successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to initialize git repository: {e.stderr.decode()}")
        raise

if __name__ == "__main__":
    main()