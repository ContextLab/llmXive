import os
import sys
from pathlib import Path
from typing import List

def create_directories() -> None:
    """
    Create the standard project directory structure.
    Ensures all required directories for code, data, tests, and specs exist.
    """
    base_path = Path(__file__).resolve().parent.parent
    
    # Define relative paths as per T001a specification
    directories: List[Path] = [
        base_path / "code",
        base_path / "data" / "raw",
        base_path / "data" / "curated",
        base_path / "data" / "results",
        base_path / "tests" / "unit",
        base_path / "tests" / "integration",
        base_path / "tests" / "contract",
        base_path / "specs" / "001-llmxive-follow-up-extending-swe-explore" / "contracts",
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path}")

    if created_count > 0:
        print(f"Successfully created {created_count} directories.")
    else:
        print("All directories already existed.")

def main() -> None:
    """Entry point for the project structure setup."""
    print("Starting project structure creation...")
    create_directories()
    print("Project structure creation complete.")

if __name__ == "__main__":
    main()
