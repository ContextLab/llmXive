import os
import sys
from pathlib import Path

def setup_directories():
    """
    Creates the required directory structure for the llmXive project.
    
    Directories created:
    - data/raw
    - data/processed
    - data/interim
    - data/results
    - code/
    - tests/
    
    Returns:
        Path: The project root path where directories were created.
    """
    # Determine project root based on the location of this script
    # Assuming this script is in <project_root>/code/
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "interim",
        project_root / "data" / "results",
        project_root / "code",
        project_root / "tests",
    ]

    created_count = 0
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"\nSetup complete. {created_count} new directories created.")
    return project_root

def main():
    """Entry point for running the directory setup script."""
    print("Initializing project directory structure...")
    setup_directories()

if __name__ == "__main__":
    main()
