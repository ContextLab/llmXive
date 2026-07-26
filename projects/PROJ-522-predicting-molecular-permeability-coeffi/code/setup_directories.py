import os
import sys
from pathlib import Path

def create_directories():
    """
    Initialize project directory structure for the molecular permeability project.
    Creates all required data, code, and test directories in a single atomic operation.
    """
    # Define the project root (assuming code/ is inside the project root)
    # We need to go up one level from code/ to find the project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    # Define all required directories relative to project root
    directories = [
        "data/raw",
        "data/processed",
        "code/models",
        "code/analysis",
        "code/utils",
        "code/config",
        "tests/contract",
        "tests/unit",
        "tests/integration"
    ]

    created_count = 0
    skipped_count = 0

    print(f"Initializing project structure at: {project_root}")

    for dir_path in directories:
        full_path = project_root / dir_path
        
        if full_path.exists():
            print(f"  [SKIP] {dir_path} already exists")
            skipped_count += 1
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  [CREATE] {dir_path}")
            created_count += 1

    print(f"\nDirectory initialization complete:")
    print(f"  Created: {created_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"  Total:   {len(directories)}")

    # Verify all directories exist
    all_exist = all((project_root / d).exists() for d in directories)
    
    if all_exist:
        print("\n[SUCCESS] All required directories verified.")
        return True
    else:
        print("\n[ERROR] Some directories failed to create.")
        return False

def main():
    """Entry point for directory initialization script."""
    success = create_directories()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
