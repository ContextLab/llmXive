"""
Task T008: Initialize Git repository and create .gitignore.

This script automates the initialization of the git repository,
creation of the .gitignore file, and the initial commit.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], cwd: Path | None = None) -> None:
    """Run a shell command and raise on failure."""
    try:
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        stderr_output = e.stderr.decode('utf-8', errors='replace')
        stdout_output = e.stdout.decode('utf-8', errors='replace')
        print(f"Command failed: {' '.join(cmd)}")
        print(f"stdout: {stdout_output}")
        print(f"stderr: {stderr_output}")
        raise RuntimeError(f"Git command failed: {e}") from e

def ensure_gitignore(root: Path) -> None:
    """Ensure .gitignore exists with required patterns."""
    gitignore_path = root / ".gitignore"
    
    required_patterns = [
        "data/",
        "__pycache__/",
        "*.pyc",
        "*.log"
    ]

    if gitignore_path.exists():
        content = gitignore_path.read_text()
        missing = [p for p in required_patterns if p not in content]
        if missing:
            print(f"Updating .gitignore with missing patterns: {missing}")
            with open(gitignore_path, "a") as f:
                f.write("\n# Added by T008\n")
                for p in missing:
                    f.write(f"{p}\n")
        else:
            print(".gitignore already contains all required patterns.")
    else:
        print("Creating new .gitignore")
        with open(gitignore_path, "w") as f:
            f.write("# Data artifacts\n")
            f.write("data/\n\n")
            f.write("# Python cache\n")
            f.write("__pycache__/\n")
            f.write("*.pyc\n\n")
            f.write("# Logs\n")
            f.write("*.log\n")

def main() -> None:
    root = Path(__file__).resolve().parent.parent
    print(f"Working directory: {root}")

    # 1. Ensure .gitignore exists and has correct content
    ensure_gitignore(root)

    # 2. Initialize git repo if not already initialized
    git_dir = root / ".git"
    if not git_dir.exists():
        print("Initializing git repository...")
        run_command(["git", "init"], cwd=root)
    else:
        print("Git repository already initialized.")

    # 3. Add files
    print("Adding files to git...")
    run_command(["git", "add", "."], cwd=root)

    # 4. Commit
    print("Committing initial project structure...")
    # Configure user if not set (local to repo or global)
    try:
        run_command(["git", "config", "user.email", "pipeline@llmxive.local"], cwd=root)
        run_command(["git", "config", "user.name", "llmXive Pipeline"], cwd=root)
    except RuntimeError:
        pass # Ignore if git config fails, might be in CI with no user

    run_command(
        ["git", "commit", "-m", "Initial project structure"],
        cwd=root
    )

    print("Task T008 completed successfully.")

if __name__ == "__main__":
    main()