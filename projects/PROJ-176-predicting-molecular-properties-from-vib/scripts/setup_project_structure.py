"""
Script to explicitly create the project directory structure.
This ensures the file system matches the implementation plan.
"""
import os
from pathlib import Path

def main():
    root = Path(".")
    
    # Define required directories
    directories = [
        root / "code",
        root / "tests",
        root / "data" / "raw",
        root / "data" / "preprocessed",
        root / "data" / "external",
        root / "specs" / "001-predicting-molecular-properties-from-vib",
        root / "contracts",
        root / "state",
        root / "results",
        root / "runs",
        root / "code" / "utils",
        root / "code" / "data",
        root / "code" / "models",
        root / "code" / "evaluation",
        root / "code" / "scripts",
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory exists: {directory}")
    
    # Create .gitkeep files to ensure directories are tracked by git
    for directory in directories:
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep in: {directory}")

    print(f"\nProject structure setup complete. Created {created_count} new directories.")

if __name__ == "__main__":
    main()