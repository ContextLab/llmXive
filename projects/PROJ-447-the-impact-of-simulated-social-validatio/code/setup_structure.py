import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the detailed directory structure for the project.
    
    Creates the following directories relative to the project root:
    - code/data, code/analysis, code/viz, code/utils
    - data/raw, data/processed
    - tests/unit, tests/integration
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    # Define the base project root
    # The script is expected to be run from the project root: projects/PROJ-447-the-impact-of-simulated-social-validation/
    base_path = Path(__file__).resolve().parent.parent
    
    # Define the directory structure to create
    directories = [
        "code/data",
        "code/analysis",
        "code/viz",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration"
    ]
    
    created_count = 0
    failed_count = 0
    
    print(f"Creating directories relative to: {base_path}")
    
    for dir_path in directories:
        full_path = base_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Created: {full_path}")
            created_count += 1
        except OSError as e:
            print(f"  ✗ Failed to create {full_path}: {e}")
            failed_count += 1
    
    print(f"\nSummary: {created_count} directories created, {failed_count} failed.")
    
    if failed_count > 0:
        return False
    return True

def main():
    """Main entry point for the script."""
    success = create_directories()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()