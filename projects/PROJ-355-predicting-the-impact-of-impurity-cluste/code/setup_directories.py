import os
import sys
from pathlib import Path
from setup_project import ensure_directory, create_gitkeep

def setup_directories():
    """
    Creates the required directory structure for the project:
    data/raw, data/processed, results, tests/unit, tests/integration.
    Also creates .gitkeep files in each to ensure they are tracked by git.
    """
    # Get project root from config
    try:
        from config import get_project_root
        project_root = get_project_root()
    except ImportError:
        # Fallback if config is not yet available or imported differently
        project_root = Path(__file__).resolve().parent.parent

    directories = [
        "data/raw",
        "data/processed",
        "results",
        "tests/unit",
        "tests/integration"
    ]

    created = []
    for dir_path in directories:
        full_path = project_root / dir_path
        if ensure_directory(full_path):
            create_gitkeep(full_path)
            created.append(str(full_path))
    
    return created

def main():
    """Entry point for running the setup script."""
    print("Setting up project directory structure...")
    created_dirs = setup_directories()
    if created_dirs:
        print(f"Created directories and .gitkeep files:")
        for d in created_dirs:
            print(f"  - {d}")
    else:
        print("All directories already exist.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
