"""
Script to initialize the project directory structure.
Implements T002: Create project structure per implementation plan.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required top-level directories: code/, tests/, data/.
    Requirement: Execute os.makedirs('code/', exist_ok=True), etc.
    """
    root = Path.cwd()
    dirs_to_create = [
        root / "code",
        root / "tests",
        root / "data"
    ]

    for dir_path in dirs_to_create:
        os.makedirs(dir_path, exist_ok=True)
        # Verify creation immediately as per robust implementation patterns
        assert dir_path.is_dir(), f"Failed to create directory: {dir_path}"
        print(f"Verified directory: {dir_path}")

    return True

def main():
    """Entry point for script execution."""
    print("Initializing project structure for T002...")
    success = create_directories()
    if success:
        print("Project structure initialization complete.")
        return 0
    else:
        print("Project structure initialization failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())