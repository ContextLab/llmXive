"""
Script to initialize the project directory structure for PROJ-189.
This script creates the required folders and placeholder files (.gitkeep)
to ensure the directory tree exists in version control.
"""
import os
from pathlib import Path

def main():
    # Define the root project directory
    root = Path("projects/PROJ-189-investigating-the-correlation-between-gu")
    
    # Define all required subdirectories
    dirs = [
        "data/raw",
        "data/processed",
        "data/models",
        "code",
        "code/utils",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "docs",
    ]

    print(f"Initializing project structure at: {root}")

    # Create directories
    for dir_path in dirs:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {full_path}")

    # Create .gitkeep files in data directories to ensure they are tracked by git
    # even if they are empty.
    data_dirs = ["data/raw", "data/processed", "data/models"]
    for data_dir in data_dirs:
        file_path = root / data_dir / ".gitkeep"
        file_path.write_text("# This file ensures the directory is tracked by git.\n")
        print(f"  Created: {file_path}")

    # Create .gitkeep files in test and code utility directories
    empty_dirs = [
        "code/utils",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "docs",
    ]
    for d in empty_dirs:
        file_path = root / d / ".gitkeep"
        file_path.write_text("# This file ensures the directory is tracked by git.\n")
        print(f"  Created: {file_path}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()