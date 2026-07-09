"""
Task T005: Create required project directories.

This script initializes the directory structure for the meta-analysis pipeline,
creating folders for search results, screening data, harmonized data, and final results.
"""
import os
from pathlib import Path

def setup_directories():
    """Create the required directory structure for the project."""
    # Define relative paths based on project conventions
    base_dir = Path(__file__).resolve().parent.parent
    
    directories = [
        base_dir / "data" / "search_results",
        base_dir / "data" / "screening",
        base_dir / "data" / "harmonized",
        base_dir / "results",
        base_dir / "results" / "figures",
        base_dir / "results" / "robustness",
        base_dir / "state"
    ]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nSetup complete. Created {created_count} new directories.")
    return True

if __name__ == "__main__":
    setup_directories()