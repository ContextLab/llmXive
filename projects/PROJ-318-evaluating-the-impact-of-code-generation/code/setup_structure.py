"""
Project Structure Setup Script.

This script creates the required directory structure for the llmXive project
and ensures all necessary directories exist with .gitkeep files for version control.
"""
import os
import sys
from pathlib import Path


def create_directories():
    """Create the required directory structure for the project."""
    # Define the base directory (project root)
    base_dir = Path(".")

    # Define the required directories relative to the base
    required_dirs = [
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
    existing_dirs = []

    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        
        if full_path.exists():
            existing_dirs.append(dir_path)
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            print(f"Created directory: {dir_path}")

    return created_dirs, existing_dirs


def create_gitkeep_files():
    """Create .gitkeep files in all required directories to ensure they are tracked by git."""
    base_dir = Path(".")
    
    required_dirs = [
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

    created_files = []
    existing_files = []

    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        gitkeep_path = full_path / ".gitkeep"
        
        if gitkeep_path.exists():
            existing_files.append(str(gitkeep_path))
        else:
            gitkeep_path.touch()
            created_files.append(str(gitkeep_path))
            print(f"Created .gitkeep file: {gitkeep_path}")

    return created_files, existing_files


def verify_structure():
    """Verify that all required directories exist."""
    base_dir = Path(".")
    
    required_dirs = [
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

    verification_results = {}
    all_exist = True

    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        exists = full_path.is_dir()
        verification_results[dir_path] = exists
        
        if not exists:
            all_exist = False
            print(f"ERROR: Directory missing: {dir_path}")
        else:
            print(f"Verified: {dir_path} exists")

    return verification_results, all_exist


def main():
    """Main entry point for the setup script."""
    print("Starting project structure setup...")
    print("-" * 50)
    
    # Step 1: Create directories
    print("\nStep 1: Creating directories...")
    created_dirs, existing_dirs = create_directories()
    print(f"Created {len(created_dirs)} new directories.")
    print(f"Found {len(existing_dirs)} existing directories.")
    
    # Step 2: Create .gitkeep files
    print("\nStep 2: Creating .gitkeep files...")
    created_files, existing_files = create_gitkeep_files()
    print(f"Created {len(created_files)} new .gitkeep files.")
    print(f"Found {len(existing_files)} existing .gitkeep files.")
    
    # Step 3: Verify structure
    print("\nStep 3: Verifying structure...")
    verification_results, all_exist = verify_structure()
    
    print("-" * 50)
    if all_exist:
        print("SUCCESS: All required directories exist and are properly initialized.")
        return 0
    else:
        print("FAILURE: Some directories are missing. Please check the error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())