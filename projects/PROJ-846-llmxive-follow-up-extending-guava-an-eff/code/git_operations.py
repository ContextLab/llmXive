import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_git_command(command: list, cwd: Optional[Path] = None) -> tuple:
    """
    Execute a git command and return (stdout, stderr, return_code).
    """
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout, result.stderr, result.returncode
    except FileNotFoundError:
        print("Error: git command not found. Please ensure git is installed and in PATH.")
        sys.exit(1)


def init_repository(repo_path: Path) -> bool:
    """
    Initialize a new Git repository at the specified path.
    """
    if not repo_path.exists():
        repo_path.mkdir(parents=True, exist_ok=True)

    stdout, stderr, code = run_git_command(["git", "init"], cwd=repo_path)
    if code != 0:
        print(f"Error initializing git repo: {stderr}")
        return False
    print(f"Initialized empty Git repository in {repo_path}/.git")
    return True


def stage_all_files(repo_path: Path) -> bool:
    """
    Stage all files in the repository for commit.
    """
    stdout, stderr, code = run_git_command(["git", "add", "."], cwd=repo_path)
    if code != 0:
        print(f"Error staging files: {stderr}")
        return False
    return True


def commit_changes(repo_path: Path, message: str) -> bool:
    """
    Commit all staged changes with the provided message.
    """
    stdout, stderr, code = run_git_command(
        ["git", "commit", "-m", message],
        cwd=repo_path
    )
    if code != 0:
        # Check if there are no changes to commit
        if "nothing to commit" in stderr:
            print("No changes to commit.")
            return True
        print(f"Error committing changes: {stderr}")
        return False
    
    # Verify commit history
    stdout, _, code = run_git_command(["git", "log", "--oneline", "-1"], cwd=repo_path)
    if code == 0:
        print(f"Latest commit: {stdout.strip()}")
    
    return True


def add_remote(repo_path: Path, remote_name: str, remote_url: str) -> bool:
    """
    Add a remote repository.
    """
    stdout, stderr, code = run_git_command(
        ["git", "remote", "add", remote_name, remote_url],
        cwd=repo_path
    )
    if code != 0:
        if "remote origin already exists" in stderr:
            print(f"Remote '{remote_name}' already exists, skipping add.")
            return True
        print(f"Error adding remote: {stderr}")
        return False
    print(f"Added remote '{remote_name}'")
    return True
