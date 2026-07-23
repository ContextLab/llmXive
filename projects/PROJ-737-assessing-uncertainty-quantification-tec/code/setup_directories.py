import os
import sys
from pathlib import Path

def main():
    """
    Creates the required directory structure for the llmXive project.
    Ensures all paths listed in tasks.md T001a exist on disk.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    # Define the directories required by T001a
    # Note: 'code' and 'tests' are already present as packages, but we ensure subdirs exist.
    directories = [
        "data/raw",
        "data/processed",
        "code/models",
        "code/metrics",
        "code/stats",
        "code/utils",
        "results",
        "tests/unit",
        "tests/integration"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_name in directories:
        full_path = project_root / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path.relative_to(project_root)}")
        else:
            existing_count += 1
            print(f"Directory already exists: {full_path.relative_to(project_root)}")
    
    print(f"Directory setup complete. Created: {created_count}, Existing: {existing_count}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
