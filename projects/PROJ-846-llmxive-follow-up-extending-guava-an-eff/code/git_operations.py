import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

def run_git_command(command: list, cwd: Optional[Path] = None) -> str:
    """Execute a git command and return the output."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e.stderr}", file=sys.stderr)
        raise

def init_repository(repo_path: Path) -> None:
    """Initialize a new git repository."""
    run_git_command(['git', 'init'], cwd=repo_path)

def stage_all_files(repo_path: Path) -> None:
    """Stage all files in the repository."""
    run_git_command(['git', 'add', '.'], cwd=repo_path)

def commit_changes(repo_path: Path, message: str) -> str:
    """Commit staged changes with the given message."""
    return run_git_command(['git', 'commit', '-m', message], cwd=repo_path)

def add_remote(repo_path: Path, name: str, url: str) -> None:
    """Add a remote repository."""
    run_git_command(['git', 'remote', 'add', name, url], cwd=repo_path)
