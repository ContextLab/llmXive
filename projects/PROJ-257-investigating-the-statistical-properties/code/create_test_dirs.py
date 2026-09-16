import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the tests/ directory structure at the repository root.
    Creates subdirectories: unit, integration, contract
    Creates a .gitkeep file in tests/ to ensure the directory is tracked by git.
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Determine project root (assumed to be where this script is run from or parent of code/)
    # We'll assume the script is run from the project root
    project_root = Path.cwd()
    tests_dir = project_root / "tests"
    
    # Create subdirectories
    subdirs = ["unit", "integration", "contract"]
    for subdir in subdirs:
        subdir_path = tests_dir / subdir
        subdir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {subdir_path}")
    
    # Create .gitkeep in tests/
    gitkeep_path = tests_dir / ".gitkeep"
    gitkeep_path.touch()
    print(f"Created .gitkeep: {gitkeep_path}")
    
    # Verify creation
    if tests_dir.exists() and gitkeep_path.exists():
        print("Verification: tests/ directory and .gitkeep exist.")
        # List contents of tests/
        contents = list(tests_dir.iterdir())
        print(f"Contents of tests/: {[item.name for item in contents]}")
        return True
    else:
        print("Error: Verification failed. tests/ directory or .gitkeep missing.")
        return False

def main():
    """Main entry point for the script."""
    success = create_directories()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()