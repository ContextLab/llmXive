"""
Git operations utility module.

Provides functions to interact with git repositories programmatically.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_git_command(args: list[str], cwd: Optional[Path] = None) -> str:
    """
    Run a git command and return the output.

    Args:
        args: List of git command arguments (excluding 'git').
        cwd: Working directory for the command.

    Returns:
        Standard output of the command.

    Raises:
        subprocess.CalledProcessError: If the command fails.
    """
    cmd = ["git"] + args
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout


def init_repository(cwd: Optional[Path] = None) -> None:
    """
    Initialize a new git repository.

    Args:
        cwd: Working directory for the command. Defaults to current directory.
    """
    run_git_command(["init"], cwd=cwd)
    print(f"Initialized git repository in {cwd or Path.cwd()}")


def stage_all_files(cwd: Optional[Path] = None) -> None:
    """
    Stage all files in the repository.

    Args:
        cwd: Working directory for the command.
    """
    run_git_command(["add", "."], cwd=cwd)
    print("Staged all files.")


def commit_changes(message: str, cwd: Optional[Path] = None) -> None:
    """
    Commit staged changes with a message.

    Args:
        message: Commit message.
        cwd: Working directory for the command.
    """
    run_git_command(["commit", "-m", message], cwd=cwd)
    print(f"Committed changes: {message}")


def add_remote(name: str, url: str, cwd: Optional[Path] = None) -> None:
    """
    Add a remote repository.

    Args:
        name: Remote name (e.g., 'origin').
        url: Remote URL.
        cwd: Working directory for the command.
    """
    run_git_command(["remote", "add", name, url], cwd=cwd)
    print(f"Added remote '{name}'")
