"""
T001: Create project structure per implementation plan.

This script creates the necessary directory structure for the 
Statistical Analysis of Publicly Available Textual Data project.

Directories created:
- code/
- data/raw/
- data/processed/
- data/interim/
- data/results/
- tests/unit/
- tests/contract/
- tests/integration/
- specs/001-statistical-cognitive-decline/contracts/
"""

import os
import sys

def create_directory(path: str) -> bool:
    """
    Create a directory if it doesn't exist.
    
    Args:
        path: The directory path to create.
        
    Returns:
        True if directory was created or already exists, False on error.
    """
    try:
        os.makedirs(path, exist_ok=True)
        print(f"✓ Created/verified: {path}")
        return True
    except OSError as e:
        print(f"✗ Failed to create {path}: {e}")
        return False

def main():
    """Create all required project directories."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define all required directories relative to project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/interim",
        "data/results",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "specs/001-statistical-cognitive-decline/contracts",
    ]
    
    print(f"Creating project structure in: {base_dir}")
    print("-" * 50)
    
    success_count = 0
    failure_count = 0
    
    for dir_path in directories:
        full_path = os.path.join(base_dir, dir_path)
        if create_directory(full_path):
            success_count += 1
        else:
            failure_count += 1
    
    print("-" * 50)
    print(f"Summary: {success_count} directories created/verified, {failure_count} failed")
    
    if failure_count > 0:
        print("ERROR: Some directories could not be created.")
        sys.exit(1)
    else:
        print("SUCCESS: Project structure created successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()