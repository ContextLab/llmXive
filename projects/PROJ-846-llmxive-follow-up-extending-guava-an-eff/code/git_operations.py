import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

def run_git_command(args: list[str], cwd: Optional[Path] = None) -> tuple[str, str, int]:
    """
    Run a git command and return stdout, stderr, and return code.
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout, result.stderr, result.returncode
    except FileNotFoundError:
        return "", "git: command not found", 127

def init_repository(cwd: Path) -> tuple[str, str, int]:
    """
    Initialize a git repository in the specified directory.
    """
    return run_git_command(["init"], cwd=cwd)

def stage_all_files(cwd: Path) -> tuple[str, str, int]:
    """
    Stage all files in the repository.
    """
    return run_git_command(["add", "."], cwd=cwd)

def commit_changes(cwd: Path, message: str) -> tuple[str, str, int]:
    """
    Commit all staged changes with the given message.
    """
    return run_git_command(["commit", "-m", message], cwd=cwd)

def add_remote(cwd: Path, name: str, url: str) -> tuple[str, str, int]:
    """
    Add a remote repository.
    """
    return run_git_command(["remote", "add", name, url], cwd=cwd)
