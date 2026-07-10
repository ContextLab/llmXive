import os
from pathlib import Path

def main():
    """
    Creates the required project directory structure for the llmXive pipeline.
    
    Creates the following directories relative to the project root:
    - data/raw
    - data/processed
    - code (if not exists, though typically this file lives here)
    - tests
    - contracts
    
    This script ensures the foundational file structure is in place before
    other pipeline stages (download, preprocess, train) can execute.
    """
    # Determine project root: parent of the 'code' directory where this script lives
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    directories_to_create = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "tests",
        project_root / "contracts",
    ]
    
    created_count = 0
    for dir_path in directories_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path.relative_to(project_root)}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path.relative_to(project_root)}")
    
    print(f"Setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    exit(main())