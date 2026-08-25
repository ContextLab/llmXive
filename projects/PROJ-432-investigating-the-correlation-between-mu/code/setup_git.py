import os
import subprocess
import sys
from pathlib import Path

def main():
    """Initialize git repository and ensure .gitignore exists."""
    project_root = Path(__file__).parent.parent

    # Initialize git repo if not already initialized
    git_dir = project_root / ".git"
    if not git_dir.exists():
        print(f"Initializing git repository in {project_root}...")
        try:
            subprocess.run(
                ["git", "init"],
                cwd=project_root,
                check=True,
                capture_output=True,
                text=True
            )
            print("Git repository initialized successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to initialize git repository: {e.stderr}")
            sys.exit(1)
    else:
        print("Git repository already initialized.")

    # Ensure .gitignore exists
    gitignore_path = project_root / ".gitignore"
    if not gitignore_path.exists():
        print(f"Creating .gitignore at {gitignore_path}...")
        # We assume .gitignore is created by the task artifact,
        # but if this script runs standalone, we can create a minimal one.
        # However, per T001b, the file should be created by the artifact.
        # This script ensures it exists if the artifact was processed.
        if not gitignore_path.exists():
            print("Warning: .gitignore not found. Please ensure it is created.")
            # Create a minimal one as fallback if the artifact wasn't processed yet
            with open(gitignore_path, "w") as f:
                f.write("# Python\n__pycache__/\n*.py[cod]\n\n# Data\ndata/\n")
            print("Minimal .gitignore created.")
    else:
        print(".gitignore already exists.")

    print("Git setup complete.")

if __name__ == "__main__":
    main()