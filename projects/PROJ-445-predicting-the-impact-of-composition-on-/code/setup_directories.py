import os
import sys
from pathlib import Path

def create_directory_structure(root_dir: Path) -> None:
    """
    Create the standard project directory structure.
    """
    directories = [
        "data/raw",
        "data/processed",
        "data/residualized",
        "data/models/lofo_models",
        "artifacts",
        "state",
        "code/src/data",
        "code/src/models",
        "code/src/utils",
        "code/tests/unit",
        "code/tests/integration",
        "docs",
        "figures",
    ]

    for dir_path in directories:
        full_path = root_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure empty directories are tracked
        gitkeep = full_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
        print(f"Created directory: {full_path}")

def main() -> None:
    """
    Entry point for directory creation.
    Assumes this script is run from the project root.
    """
    root_dir = Path(__file__).resolve().parent.parent
    print(f"Creating project structure in: {root_dir}")
    create_directory_structure(root_dir)
    print("Project structure created successfully.")

if __name__ == "__main__":
    main()
