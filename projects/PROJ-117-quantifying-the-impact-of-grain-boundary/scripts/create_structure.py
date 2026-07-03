"""
Script to initialize the project directory structure for PROJ-117.
This script creates the required folders: code/, data/raw/, data/processed/, models/, artifacts/.
It is idempotent and safe to run multiple times.
"""
import os
from pathlib import Path

def create_directories():
    base_dir = Path(__file__).parent.parent
    structure = [
        "code",
        "data/raw",
        "data/processed",
        "models",
        "artifacts/reports",
        "artifacts/figures",
        "tests/unit",
        "tests/integration",
        "specs"
    ]

    for dir_path in structure:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified: {full_path}")

    # Create .gitkeep files to ensure directories are tracked by git
    keep_files = [
        "code/.gitkeep",
        "data/raw/.gitkeep",
        "data/processed/.gitkeep",
        "models/.gitkeep",
        "artifacts/reports/.gitkeep",
        "artifacts/figures/.gitkeep",
        "tests/unit/.gitkeep",
        "tests/integration/.gitkeep",
        "specs/.gitkeep"
    ]

    for keep in keep_files:
        full_path = base_dir / keep
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if not full_path.exists():
            full_path.touch()
            print(f"Created .gitkeep: {full_path}")
        else:
            print(f"Skipped existing .gitkeep: {full_path}")

if __name__ == "__main__":
    create_directories()
    print("Project structure initialization complete.")