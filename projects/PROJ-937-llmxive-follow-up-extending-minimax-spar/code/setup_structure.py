"""
Setup script to create the project directory structure.
Creates: code/, data/raw, data/processed, results, tests/unit, tests/integration
"""
import os
import sys
from pathlib import Path

def create_project_structure():
    """Create the required directory structure for the llmXive project."""
    base_path = Path(os.getcwd())
    
    # Define directories to create
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "tests/unit",
        "tests/integration"
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
    
    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    return True

def main():
    """Main entry point for the script."""
    try:
        success = create_project_structure()
        if success:
            print("SUCCESS: Directory structure created successfully.")
            sys.exit(0)
        else:
            print("ERROR: Failed to create directory structure.")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: Exception occurred during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
