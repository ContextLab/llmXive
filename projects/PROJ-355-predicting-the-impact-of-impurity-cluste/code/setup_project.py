import os
import sys
from pathlib import Path

def ensure_directory(path: Path) -> None:
    """
    Ensure the directory at `path` exists.
    Creates parent directories if necessary.
    Idempotent: does nothing if directory already exists.
    """
    path.mkdir(parents=True, exist_ok=True)

def create_gitkeep(path: Path) -> None:
    """
    Create a .gitkeep file in the directory at `path` to ensure it is tracked by git.
    Idempotent: overwrites if exists, or creates if missing.
    """
    gitkeep_file = path / ".gitkeep"
    gitkeep_file.touch(exist_ok=True)

def main() -> None:
    """
    Entry point for running setup_project as a script.
    This is a helper module; actual execution logic is in setup_directories.py.
    """
    print("setup_project module loaded. Use setup_directories.py for execution.")
