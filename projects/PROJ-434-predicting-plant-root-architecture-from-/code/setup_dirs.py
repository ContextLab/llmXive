"""
Script to create the required directory structure for the project.
This is for documentation and future automation.
"""
import os
import sys
from pathlib import Path

def main():
    """Create all required directories."""
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        project_root / "code",
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "logs",
        project_root / "tests",
        project_root / "artifacts",
        project_root / "figures",
        project_root / "code" / "utils",
        project_root / "code" / "ingestion",
        project_root / "code" / "modeling",
    ]

    for dir_path in directories:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created/Verified: {dir_path}")

    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()