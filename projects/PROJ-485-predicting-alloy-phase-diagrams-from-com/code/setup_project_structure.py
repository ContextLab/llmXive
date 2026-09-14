import os
import sys
from typing import List

def create_directories() -> None:
    """Create the project directory structure for PROJ-485."""
    base_dirs: List[str] = [
        "code",
        "code/ingest",
        "code/features",
        "code/models",
        "code/viz",
        "code/utils",
        "tests",
    ]
    
    created_count = 0
    for dir_path in base_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Setup complete. Created {created_count} new directories.")

def main() -> None:
    """Entry point for the script."""
    create_directories()

if __name__ == "__main__":
    main()