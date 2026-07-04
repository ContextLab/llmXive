"""
Project Structure Initialization Script.

This script creates the required directory structure for the llmXive
research pipeline as specified in the implementation plan.

Directories created:
- code/ (already exists but ensured)
- data/raw/
- data/processed/
- results/
- logs/
"""
import os
import sys
from pathlib import Path


def main():
    """Create the project directory structure."""
    # Define the root directory (current working directory or project root)
    root = Path.cwd()
    
    # Define required directories relative to root
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "logs"
    ]
    
    created_count = 0
    existing_count = 0
    
    print(f"Initializing project structure at: {root}")
    
    for dir_path in required_dirs:
        full_path = root / dir_path
        
        if full_path.exists():
            if full_path.is_dir():
                print(f"  [OK] Directory exists: {dir_path}")
                existing_count += 1
            else:
                print(f"  [ERROR] Path exists but is not a directory: {dir_path}")
                sys.exit(1)
        else:
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"  [CREATED] {dir_path}")
                created_count += 1
            except OSError as e:
                print(f"  [ERROR] Failed to create {dir_path}: {e}")
                sys.exit(1)
    
    # Create .gitkeep files to ensure directories are tracked by git
    gitkeep_files = [
        "data/raw/.gitkeep",
        "data/processed/.gitkeep",
        "results/.gitkeep",
        "logs/.gitkeep"
    ]
    
    for file_path in gitkeep_files:
        full_path = root / file_path
        if not full_path.exists():
            try:
                full_path.touch()
                print(f"  [CREATED] {file_path}")
            except OSError as e:
                print(f"  [WARNING] Failed to create {file_path}: {e}")
    
    print(f"\nSummary: {created_count} directories created, {existing_count} already existed.")
    print("Project structure initialization complete.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
