import os
import sys
from pathlib import Path
from typing import List

def create_directories(base_path: Path) -> List[Path]:
    """
    Create the required directory structure for the project.
    Returns a list of created directory paths.
    """
    # Define relative paths to create
    relative_paths = [
        "code",
        "code/utils",
        "data/raw",
        "data/raw/repos",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "state",
        "logs"
    ]

    created_dirs = []
    for rel_path in relative_paths:
        full_path = base_path / rel_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(full_path)
        print(f"Created directory: {full_path}")

    return created_dirs

def create_gitkeep_files(directories: List[Path]) -> int:
    """
    Create .gitkeep files in all provided directories.
    Returns the count of .gitkeep files created.
    """
    count = 0
    for directory in directories:
        gitkeep_path = directory / ".gitkeep"
        # Create an empty file or touch it
        gitkeep_path.touch(exist_ok=True)
        count += 1
        print(f"Created .gitkeep in: {directory}")
    return count

def verify_structure(base_path: Path) -> bool:
    """
    Verify that all required directories and .gitkeep files exist.
    Returns True if verification passes, False otherwise.
    """
    relative_paths = [
        "code",
        "code/utils",
        "data/raw",
        "data/raw/repos",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "state",
        "logs"
    ]

    all_exist = True
    for rel_path in relative_paths:
        full_path = base_path / rel_path
        gitkeep_path = full_path / ".gitkeep"

        if not full_path.is_dir():
            print(f"ERROR: Directory missing: {full_path}")
            all_exist = False
        elif not gitkeep_path.exists():
            print(f"ERROR: .gitkeep missing in: {full_path}")
            all_exist = False
        else:
            print(f"OK: {full_path} contains .gitkeep")

    return all_exist

def main():
    """
    Main entry point to create structure and .gitkeep files.
    """
    base_path = Path.cwd()
    print(f"Working directory: {base_path}")

    # Step 1: Create directories
    print("\n--- Creating Directories ---")
    directories = create_directories(base_path)

    # Step 2: Create .gitkeep files
    print("\n--- Creating .gitkeep Files ---")
    gitkeep_count = create_gitkeep_files(directories)

    # Step 3: Verification
    print("\n--- Verifying Structure ---")
    if verify_structure(base_path):
        print("\n✅ Verification PASSED: All directories and .gitkeep files exist.")
        # Final verification command simulation
        print(f"Verification count: {gitkeep_count} .gitkeep files found.")
        return 0
    else:
        print("\n❌ Verification FAILED: Some files or directories are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())