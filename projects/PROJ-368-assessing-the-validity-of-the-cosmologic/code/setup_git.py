"""
Git repository initialization and .gitignore management.
Implements Task T008: Initialize git repository.
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd: list, cwd: Path = None) -> None:
    """Execute a shell command and raise on failure."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}", file=sys.stderr)
        print(f"Error output: {e.stderr}", file=sys.stderr)
        raise

def ensure_gitignore(root: Path) -> None:
    """Create or update .gitignore with required patterns."""
    gitignore_path = root / ".gitignore"
    required_patterns = [
        "data/",
        "__pycache__/",
        "*.pyc",
        "*.log"
    ]

    existing_patterns = set()
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    existing_patterns.add(stripped)

    needs_update = False
    new_lines = []

    # Check if we need to add patterns
    for pattern in required_patterns:
        if pattern not in existing_patterns:
            new_lines.append(pattern)
            needs_update = True

    if needs_update:
        with open(gitignore_path, 'a') as f:
            if new_lines and not gitignore_path.read_text().endswith('\n'):
                f.write('\n')
            for line in new_lines:
                f.write(f"{line}\n")
        print(f"Updated .gitignore with new patterns: {new_lines}")
    else:
        print(".gitignore already contains all required patterns.")

def main() -> None:
    """Initialize git repo, ensure .gitignore, add files, and commit."""
    root = Path.cwd()
    
    print(f"Initializing Git repository in {root}...")
    
    # Initialize git if not already done
    git_dir = root / ".git"
    if not git_dir.exists():
        run_command(["git", "init"], cwd=root)
        print("Git repository initialized.")
    else:
        print("Git repository already exists.")

    # Ensure .gitignore exists and has required patterns
    ensure_gitignore(root)

    # Add all files
    print("Adding all files to git...")
    run_command(["git", "add", "."], cwd=root)

    # Commit
    print("Committing initial project structure...")
    run_command(["git", "commit", "-m", "Initial project structure"], cwd=root)

    print("Git setup completed successfully.")

if __name__ == "__main__":
    main()