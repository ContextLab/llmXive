"""
Create state directory structure at repository root.

This script creates the state/ directory and its subdirectories
for storing project state, checkpoints, and artifacts.

Usage:
    python code/setup/create_state_dirs.py
"""
import os
from pathlib import Path


def create_state_directories(root_dir: str = ".") -> None:
    """
    Create state directory structure at the specified root directory.

    Creates:
        - state/
        - state/projects/

    Args:
        root_dir: The project root directory (defaults to current directory)
    """
    root = Path(root_dir).resolve()
    state_dir = root / "state"
    projects_dir = state_dir / "projects"

    # Create state directory if it doesn't exist
    if not state_dir.exists():
        state_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {state_dir}")
    else:
        print(f"Directory already exists: {state_dir}")

    # Create projects subdirectory if it doesn't exist
    if not projects_dir.exists():
        projects_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {projects_dir}")
    else:
        print(f"Directory already exists: {projects_dir}")

    print(f"State directory structure ready at: {state_dir}")


if __name__ == "__main__":
    create_state_directories()
