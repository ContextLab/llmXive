"""
Setup script to create the directory structure for the llmXive project.
Creates the following directories relative to the project root:
- code/
- code/src/
- code/tests/
- code/data/raw/
- code/data/processed/
- code/data/results/
"""
import os
from pathlib import Path

def main():
    """Create the required directory structure."""
    # Define the base directory (project root)
    base_dir = Path(__file__).parent.parent
    
    # Define relative paths to create
    directories = [
        "code",
        "code/src",
        "code/tests",
        "code/data/raw",
        "code/data/processed",
        "code/data/results"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    # Verification step: Ensure code/src exists
    src_path = base_dir / "code" / "src"
    if not src_path.exists():
        print("ERROR: code/src directory creation failed.")
        return 1
    
    print(f"Successfully created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())