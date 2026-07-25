"""
Project structure initialization script for PROJ-473.
Creates the required directory hierarchy: code/, data/, tests/, artifacts/.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the root directory (current working directory or project root)
    root = Path(os.getcwd())
    
    # Define required directories relative to root
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "tests",
        "tests/integration",
        "artifacts",
        "figures",
        "specs"
    ]
    
    created_count = 0
    for dir_name in directories:
        target_path = root / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
            created_count += 1
        else:
            print(f"Directory exists: {target_path}")
    
    print(f"\nProject structure initialization complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())