"""
Directory structure setup for the CiteVQA benchmark extension project.
Creates the required directory hierarchy as per the implementation plan.
"""
import os
import sys
from pathlib import Path


def create_directory_structure():
    """
    Creates the standard project directory structure:
    - code/
    - tests/
    - data/
      - raw/
      - processed/
      - results/
      - logs/
    - scripts/
    
    Ensures all directories exist and handles any existing paths gracefully.
    """
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define the directory structure relative to the base
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "data/logs",
        "scripts"
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        
        if full_path.exists():
            if full_path.is_dir():
                skipped_count += 1
                print(f"Directory already exists: {full_path}")
            else:
                raise FileExistsError(f"Path exists but is not a directory: {full_path}")
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
    
    print(f"\nDirectory setup complete.")
    print(f"Created: {created_count} directories")
    print(f"Skipped (already existed): {skipped_count} directories")
    
    return True


def main():
    """Entry point for the directory setup script."""
    print("Initializing directory structure for CiteVQA project...")
    try:
        create_directory_structure()
        print("Success.")
        sys.exit(0)
    except Exception as e:
        print(f"Error during directory creation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()