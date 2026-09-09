"""
Script to create the project directory structure.
This script ensures all required directories exist for the llmXive pipeline.
"""
import os
from pathlib import Path

def main():
    """Create the required directory structure."""
    root = Path(__file__).parent.parent
    
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "state",
        "code/utils",
        "code/data",
        "code/analysis",
        "tests/unit",
        "tests/integration",
        "figures",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path.relative_to(root)}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path.relative_to(root)}")
    
    print(f"\nTotal new directories created: {created_count}")
    print("Directory structure verification complete.")

if __name__ == "__main__":
    main()