"""
Script to verify and initialize the project directory structure.
Run this script to ensure all required directories exist.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root relative to this script's location
    # Assuming script is in projects/PROJ-990-.../scripts/
    base_dir = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        base_dir / "code",
        base_dir / "tests",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "models",
        base_dir / "figures",
        base_dir / "specs",
    ]

    print(f"Initializing project structure at: {base_dir}")
    
    created_count = 0
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created directory: {dir_path.relative_to(base_dir)}")
            created_count += 1
        else:
            print(f"  Directory exists: {dir_path.relative_to(base_dir)}")

    # Create placeholder files to ensure git tracks directories
    placeholders = [
        base_dir / "data" / "raw" / ".gitkeep",
        base_dir / "data" / "processed" / ".gitkeep",
        base_dir / "models" / ".gitkeep",
        base_dir / "figures" / ".gitkeep",
    ]

    for placeholder in placeholders:
        if not placeholder.exists():
            placeholder.touch()
            print(f"  Created placeholder: {placeholder.relative_to(base_dir)}")
        else:
            print(f"  Placeholder exists: {placeholder.relative_to(base_dir)}")

    if created_count == 0:
        print("Project structure already complete.")
    else:
        print(f"Successfully created {created_count} directories.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
