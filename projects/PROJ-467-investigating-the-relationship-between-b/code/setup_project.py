"""
Project structure initialization script.
Creates the necessary directory hierarchy for the brainnet project.
"""
import os
import sys
from pathlib import Path


def main():
    """
    Creates the required project directories relative to the project root.
    Exits with code 0 on success, 1 on failure.
    """
    # Define the directory structure relative to the project root
    # The script is located at code/setup_project.py, so we go up one level
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "src/brainnet",
        "tests/unit",
        "tests/contract",
        "data/processed",
        "data/raw",
        "results/figures",
        "metadata",
        "contracts"
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"Initializing project structure at: {project_root}")
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"Created: {full_path}")
                created_count += 1
            except OSError as e:
                print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Already exists: {full_path}")
            skipped_count += 1
    
    print(f"\nProject structure initialization complete.")
    print(f"Created {created_count} new directories.")
    print(f"Skipped {skipped_count} existing directories.")
    
    # Verify existence of all directories
    missing = []
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing.append(str(full_path))
    
    if missing:
        print(f"ERROR: The following directories were not created: {missing}", file=sys.stderr)
        sys.exit(1)
    
    print("Verification passed: All required directories exist.")
    sys.exit(0)


if __name__ == "__main__":
    main()