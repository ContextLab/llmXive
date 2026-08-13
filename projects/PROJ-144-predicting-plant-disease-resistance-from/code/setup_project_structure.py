"""
Script to create the project directory structure for the llmXive plant disease resistance pipeline.
"""
import os
import sys
from pathlib import Path

def create_structure():
    """
    Creates the required directory structure for the project.
    Returns True if successful, False otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    # Define the directories to create relative to the project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/intermediate",
        "tests",
        "state",
        "results",
        "results/plots",
        "contracts"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            # Verify the directory exists and is writable
            if full_path.is_dir():
                # Try to create a temporary file to test writability
                test_file = full_path / ".write_test"
                test_file.touch()
                test_file.unlink()
                created_count += 1
            else:
                print(f"Error: Could not create directory {full_path}")
                return False
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}")
            return False
    
    print(f"Successfully created {created_count} directories.")
    return True

if __name__ == "__main__":
    success = create_structure()
    sys.exit(0 if success else 1)
