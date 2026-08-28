import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the full project directory structure as defined in the implementation plan.
    This includes code submodules, data directories, tests, and docs.
    """
    base_path = Path(".")
    
    directories = [
        # Code modules
        "code/simulation",
        "code/models",
        "code/metrics",
        "code/validation",
        "code/plots",
        "code/scripts",
        
        # Data directories
        "data/raw",
        "data/simulated",
        "data/results",
        
        # Test directories
        "tests/unit",
        "tests/integration",
        
        # Documentation
        "docs/paper"
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            skipped_count += 1
            # Optional: print(f"Directory already exists: {dir_path}")
    
    print(f"\nDirectory creation summary:")
    print(f"  Created: {created_count}")
    print(f"  Skipped (already exist): {skipped_count}")
    print(f"  Total directories: {len(directories)}")
    
    return directories

def main():
    """Entry point for the script."""
    print("Starting project structure setup...")
    create_directories()
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
