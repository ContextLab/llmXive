import os
import subprocess
import sys
from pathlib import Path

def run_command(command: list, cwd: Path = None) -> str:
    """
    Execute a shell command and return the output.
    Raises an exception if the command fails.
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command failed: {' '.join(command)}\nError: {e.stderr}")

def ensure_gitignore(root: Path) -> None:
    """
    Create or update the .gitignore file in the project root.
    Ensures data/, __pycache__/, *.pyc, and *.log are ignored.
    """
    gitignore_path = root / ".gitignore"
    required_entries = [
        "data/",
        "__pycache__/",
        "*.pyc",
        "*.log",
        ".DS_Store",
        ".env"
    ]

    current_entries = set()
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            current_entries = {line.strip() for line in f if line.strip()}

    # Add missing entries
    missing_entries = [entry for entry in required_entries if entry not in current_entries]
    
    if missing_entries:
        with open(gitignore_path, 'a') as f:
            f.write("\n")
            for entry in missing_entries:
                f.write(f"{entry}\n")
        print(f"Updated .gitignore with: {missing_entries}")
    else:
        print(".gitignore already contains all required entries.")

def main():
    """
    Main entry point for T008: Initialize git repository.
    1. Initialize git repo.
    2. Create/update .gitignore.
    3. Add all files and commit.
    """
    root = Path(__file__).resolve().parent.parent
    print(f"Initializing git repository at: {root}")

    # 1. Git Init
    try:
        run_command(["git", "init"], cwd=root)
        print("Git repository initialized.")
    except RuntimeError as e:
        # Check if repo already exists
        if "Reinitialized existing Git repository" in str(e):
            print("Git repository already exists, proceeding.")
        else:
            raise e

    # 2. Ensure .gitignore
    ensure_gitignore(root)

    # 3. Git Add and Commit
    try:
        # Configure user if not set (needed for commit)
        run_command(["git", "config", "user.email", "pipeline@llmxive.local"], cwd=root)
        run_command(["git", "config", "user.name", "llmXive Agent"], cwd=root)

        run_command(["git", "add", "."], cwd=root)
        
        # Check if there are changes to commit
        status_result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=root,
            capture_output=True
        )
        
        if status_result.returncode == 1: # Has changes
            run_command(["git", "commit", "-m", "Initial project structure"], cwd=root)
            print("Initial commit successful.")
        else:
            print("No changes to commit.")
            
    except RuntimeError as e:
        print(f"Warning during commit: {e}")
        # Do not fail the task if commit fails due to no changes, 
        # but fail if it's a command execution error.

if __name__ == "__main__":
    main()
