"""
Directory structure setup for the Social Exclusion Project.
Creates the required folder hierarchy as specified in T001a.
"""
import os
import sys
from pathlib import Path


def create_directory_structure(base_path: Path) -> None:
    """
    Creates the directory structure for the project.

    Expected structure relative to base_path:
    - projects/PROJ-382-the-impact-of-simulated-social-exclusion/code/
    - projects/PROJ-382-the-impact-of-simulated-social-exclusion/data/raw/
    - projects/PROJ-382-the-impact-of-simulated-social-exclusion/data/processed/
    - projects/PROJ-382-the-impact-of-simulated-social-exclusion/tests/
    - projects/PROJ-382-the-impact-of-simulated-social-exclusion/state/

    Args:
        base_path: The root directory where the project folder will be created.
    """
    project_name = "PROJ-382-the-impact-of-simulated-social-exclusion"
    project_root = base_path / "projects" / project_name

    # Define required directories
    directories = [
        project_root / "code",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "tests",
        project_root / "state",
    ]

    # Create directories
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

    # Create .gitkeep files to ensure directories are tracked by git
    for directory in directories:
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep in: {directory}")


def main() -> int:
    """
    Entry point for the script.
    Creates the directory structure relative to the current working directory.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        base_path = Path.cwd()
        create_directory_structure(base_path)
        print("Directory structure setup completed successfully.")
        return 0
    except Exception as e:
        print(f"Error setting up directory structure: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())