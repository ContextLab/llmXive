"""
Task T001: Initialize project directory structure.

Creates the required directory hierarchy for PROJ-582 and places .gitkeep files
in data directories to ensure they are tracked by version control.

Directory Structure:
projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/
    ├── src/
    ├── data/
    │   ├── raw/
    │   ├── processed/
    │   └── results/
    └── tests/
"""
import os
import sys
from pathlib import Path


def create_directories(base_path: Path) -> None:
    """Create the standard project directory structure."""
    structure = [
        "src",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
    ]

    for subdir in structure:
        dir_path = base_path / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")


def create_gitkeep_files(data_path: Path) -> None:
    """Create .gitkeep files in all data subdirectories."""
    data_subdirs = ["raw", "processed", "results"]

    for subdir in data_subdirs:
        dir_path = data_path / subdir
        gitkeep_path = dir_path / ".gitkeep"
        gitkeep_path.touch()
        print(f"Created .gitkeep: {gitkeep_path}")


def verify_structure(base_path: Path) -> bool:
    """Verify that all required directories exist."""
    required_dirs = [
        base_path / "src",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
        base_path / "tests",
    ]

    all_exist = all(d.is_dir() for d in required_dirs)

    if all_exist:
        print("Verification successful: All directories exist.")
    else:
        missing = [str(d) for d in required_dirs if not d.is_dir()]
        print(f"Verification failed: Missing directories: {missing}")

    return all_exist


def main() -> int:
    """Main entry point for the script."""
    # Determine the project root relative to this script's location
    # The script is expected to be in: projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/
    current_file = Path(__file__).resolve()
    project_root = current_file.parent

    print(f"Project root: {project_root}")

    try:
        create_directories(project_root)
        create_gitkeep_files(project_root / "data")
        success = verify_structure(project_root)
        return 0 if success else 1
    except Exception as e:
        print(f"Error during setup: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())