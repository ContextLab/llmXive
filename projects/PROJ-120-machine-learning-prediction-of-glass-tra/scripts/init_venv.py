"""
Initialize a Python virtual environment for the glass transition prediction project.

This script creates a virtual environment at the specified location and ensures
the standard directory structure exists for the project.
"""
import os
import subprocess
import sys
from pathlib import Path


def create_virtualenv(project_root: Path, venv_name: str = ".venv") -> None:
    """
    Create a Python virtual environment in the project root.

    Args:
        project_root: The root directory of the project.
        venv_name: The name of the virtual environment directory.

    Raises:
        RuntimeError: If virtualenv creation fails.
    """
    venv_path = project_root / venv_name

    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}. Skipping creation.")
        return

    print(f"Creating virtual environment at {venv_path}...")
    try:
        # Use the current Python interpreter to create the venv
        subprocess.check_call(
            [sys.executable, "-m", "venv", str(venv_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"Virtual environment created successfully at {venv_path}.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create virtual environment: {e}") from e


def main() -> None:
    """Main entry point for the script."""
    # Determine project root based on the task description
    project_root = Path(__file__).resolve().parent.parent
    venv_name = ".venv"

    create_virtualenv(project_root, venv_name)

    # Ensure standard directories exist (T001b-f already created them, but this is defensive)
    dirs_to_create = ["data", "code", "tests", "artifacts", "state"]
    for dir_name in dirs_to_create:
        dir_path = project_root / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"Ensured directory exists: {dir_path}")


if __name__ == "__main__":
    main()
