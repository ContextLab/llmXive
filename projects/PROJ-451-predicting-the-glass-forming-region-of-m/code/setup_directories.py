"""
Script to initialize the project directory structure for llmXive research pipeline.
This task (T001b) creates the required subdirectories: code/, data/, tests/, docs/, notebooks/.
It also creates necessary subdirectories for data (raw, processed) and .gitkeep files.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the standard project directory structure."""
    # Define the base directory (project root)
    base_dir = Path(__file__).parent.parent
    
    # Define the directories to create relative to the project root
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "data/figures",
        "tests",
        "tests/unit",
        "tests/integration",
        "docs",
        "notebooks",
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
    
    # Create .gitkeep files to ensure empty directories are tracked by git
    gitkeep_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "data/figures",
        "tests",
        "tests/unit",
        "tests/integration",
        "docs",
        "notebooks",
    ]
    
    for dir_path in gitkeep_dirs:
        full_path = base_dir / dir_path / ".gitkeep"
        if not full_path.exists():
            full_path.touch()
            print(f"Created .gitkeep in: {full_path.parent}")
        else:
            print(f".gitkeep already exists in: {full_path.parent}")
    
    print(f"\nDirectory structure initialization complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())