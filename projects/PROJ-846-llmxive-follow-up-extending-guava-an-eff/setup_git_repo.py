"""
Script to initialize the Git repository for the project.
Executes:
  1. git init
  2. git add .
  3. git commit -m "Initial commit"
"""
import os
import subprocess
import sys
from pathlib import Path

def run_git_command(command: list, cwd: Path) -> None:
    """Run a git command and raise an error if it fails."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"Executed: {' '.join(command)}")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {' '.join(command)}", file=sys.stderr)
        print(f"stderr: {e.stderr}", file=sys.stderr)
        raise RuntimeError(f"Git command failed: {e.stderr}")

def initialize_git_repository(project_root: Path) -> None:
    """Initialize git, add files, and commit."""
    git_dir = project_root / ".git"
    
    # Check if already initialized
    if git_dir.exists():
        print(f"Git repository already exists at {project_root}")
        # Optional: reset or verify state if needed, but for T001 we assume fresh or just verify
        return

    # 1. git init
    run_git_command(["git", "init"], cwd=project_root)

    # Ensure .gitignore exists before adding
    gitignore = project_root / ".gitignore"
    if not gitignore.exists():
        raise FileNotFoundError(f".gitignore not found at {gitignore}. Create it before running this script.")

    # 2. git add .
    run_git_command(["git", "add", "."], cwd=project_root)

    # 3. git commit -m "Initial commit"
    run_git_command(["git", "commit", "-m", "Initial commit"], cwd=project_root)

    print(f"Git repository initialized successfully at {project_root}")

def main() -> None:
    # Project root relative to the code/ directory
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent / "projects" / "PROJ-846-llmxive-follow-up-extending-guava-an-eff"
    
    if not project_root.exists():
        print(f"Project root not found: {project_root}", file=sys.stderr)
        sys.exit(1)

    initialize_git_repository(project_root)

if __name__ == "__main__":
    main()
