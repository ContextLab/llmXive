import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the full project directory structure as defined in tasks.md for T001.
    This includes code/, data/, tests/, and docs/ trees with .gitkeep files.
    """
    base_path = Path.cwd()

    # Define the directory tree structure
    directories = [
        # Code modules
        "code/simulation",
        "code/models",
        "code/metrics",
        "code/validation",
        "code/plots",
        "code/scripts",
        
        # Data directories
        "data/raw",
        "data/simulated",
        "data/results",
        
        # Test directories
        "tests/unit",
        "tests/integration",
        
        # Documentation
        "docs/paper"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    # Create .gitkeep files to ensure directories are tracked by git
    gitkeep_directories = [
        "data/raw",
        "data/simulated",
        "data/results",
        "docs/paper"
    ]

    for dir_path in gitkeep_directories:
        full_path = base_path / dir_path / ".gitkeep"
        if not full_path.exists():
            full_path.touch()
            print(f"Created .gitkeep: {full_path}")
        else:
            print(f".gitkeep already exists: {full_path}")

    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    return True

def main():
    """Entry point for script execution."""
    try:
        create_directories()
        return 0
    except Exception as e:
        print(f"Error setting up project structure: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
