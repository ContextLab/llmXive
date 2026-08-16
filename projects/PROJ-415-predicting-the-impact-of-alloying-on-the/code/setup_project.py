import os
import sys
from pathlib import Path
from typing import List

def create_directories(root: Path, dirs: List[str]) -> None:
    """Create directory structure if it does not exist."""
    for d in dirs:
        full_path = root / d
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def create_init_files(root: Path, dirs: List[str]) -> None:
    """Create __init__.py files in Python package directories."""
    for d in dirs:
        full_path = root / d / "__init__.py"
        # Only create if it doesn't exist to avoid overwriting user edits
        if not full_path.exists():
            full_path.touch()
            print(f"Created __init__.py: {full_path}")

def main() -> None:
    """Main entry point to setup project structure."""
    # Define the project root relative to the script location or current dir
    # Assuming script is run from project root or code/
    current_dir = Path.cwd()
    # If running from code/, go up one level
    if current_dir.name == "code":
        project_root = current_dir.parent
    else:
        project_root = current_dir

    # Define required directories per task T001
    # Directories: code, tests, data, models, reports
    # We also create subdirectories for data as per T007 requirements
    base_dirs = [
        "code",
        "code/data",
        "code/utils",
        "code/models",
        "code/validation",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "data",
        "data/raw",
        "data/curated",
        "data/artifacts",
        "data/logs",
        "models",
        "reports",
        "figures",
        "contracts",
        "specs"
    ]

    print(f"Setting up project structure at: {project_root}")
    create_directories(project_root, base_dirs)
    create_init_files(project_root, base_dirs)
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
