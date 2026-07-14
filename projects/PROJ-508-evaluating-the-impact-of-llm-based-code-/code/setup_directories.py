import os
from pathlib import Path

def create_directories():
    """
    Creates the required directory structure for the project.
    Specifically implements T010: Create docs/output directory.
    Also ensures raw and derived data directories exist if they don't already.
    """
    base_path = Path("projects/PROJ-508-evaluating-the-impact-of-llm-based-code-")
    
    # Directories to create
    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "derived",
        base_path / "docs" / "output",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    return created_count

if __name__ == "__main__":
    count = create_directories()
    print(f"Total directories created: {count}")