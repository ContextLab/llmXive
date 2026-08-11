import os
import sys
from pathlib import Path
from typing import List

def create_directories() -> None:
    """Create the required project directory structure."""
    root = Path(__file__).parent.parent
    
    # Define all required directories based on task T001a
    directories = [
        root / "code",
        root / "data" / "raw",
        root / "data" / "curated",
        root / "data" / "results",
        root / "tests" / "unit",
        root / "tests" / "integration",
        root / "tests" / "contract",
        root / "specs" / "001-llmxive-follow-up-extending-swe-explore" / "contracts",
    ]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Total directories created: {created_count}")

def main() -> None:
    """Entry point for the script."""
    create_directories()
    print("Project structure creation complete.")

if __name__ == "__main__":
    main()
