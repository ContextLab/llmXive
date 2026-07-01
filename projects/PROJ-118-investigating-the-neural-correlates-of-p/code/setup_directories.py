"""
Task T006: Setup directory structure for the project.

Ensures the following directories exist relative to the project root:
- data/raw
- data/processed
- results
- results/plots

This script is idempotent and safe to run multiple times.
"""
import os
from pathlib import Path

def setup_directories():
    """Create required project directories if they do not exist."""
    # Define the base directory (project root)
    # We assume this script is run from the project root or that the root is the parent of 'code'
    base_dir = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "results",
        "results/plots"
    ]
    
    created_count = 0
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Directory setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    setup_directories()