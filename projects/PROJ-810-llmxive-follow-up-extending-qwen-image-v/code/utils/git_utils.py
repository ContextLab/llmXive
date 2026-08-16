import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple

def check_git_initialized(repo_path: Path) -> bool:
    """Check if a Git repository is initialized at the given path."""
    git_dir = repo_path / ".git"
    return git_dir.exists() and git_dir.is_dir()

def initialize_git_repository(repo_path: Path) -> Tuple[bool, str]:
    """Initialize a Git repository at the given path if not already initialized."""
    if check_git_initialized(repo_path):
        return True, "Repository already initialized."

    try:
        subprocess.run(
            ["git", "init"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True
        )
        return True, "Repository initialized successfully."
    except subprocess.CalledProcessError as e:
        return False, f"Failed to initialize repository: {e.stderr}"
    except FileNotFoundError:
        return False, "Git is not installed or not found in PATH."

def main(repo_path: Optional[Path] = None):
    """Main entry point for Git initialization."""
    if repo_path is None:
        repo_path = Path.cwd()

    success, message = initialize_git_repository(repo_path)
    if success:
        print(message)
    else:
        raise RuntimeError(message)

    return success
