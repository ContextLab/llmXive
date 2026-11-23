"""
Project Structure Setup Script.

This script initializes the llmXive project directory structure as defined
in plan.md and tasks.md (Task T001a).

It creates the following directories at the repository root:
- code/
- data/raw/
- data/derived/
- data/validation/
- tests/
- tests/unit/

It also creates .gitkeep files in data subdirectories to ensure they are
tracked by git even when empty.
"""
import os
from pathlib import Path


def main():
    """Create the project directory structure."""
    root = Path(".")
    
    # Define the required directories
    directories = [
        "code",
        "data/raw",
        "data/derived",
        "data/validation",
        "tests",
        "tests/unit",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    # Create .gitkeep files in data subdirectories
    data_subdirs = ["data/raw", "data/derived", "data/validation"]
    for subdir in data_subdirs:
        gitkeep_path = root / subdir / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in: {subdir}")
            created_count += 1
        else:
            print(f".gitkeep already exists in: {subdir}")
    
    # Create .gitkeep in tests/unit if needed
    tests_unit_gitkeep = root / "tests" / "unit" / ".gitkeep"
    if not tests_unit_gitkeep.exists():
        tests_unit_gitkeep.touch()
        print(f"Created .gitkeep in: tests/unit")
        created_count += 1
    
    print(f"\nSetup complete. Created {created_count} new items.")
    print("Directory structure is ready for project development.")


if __name__ == "__main__":
    main()
