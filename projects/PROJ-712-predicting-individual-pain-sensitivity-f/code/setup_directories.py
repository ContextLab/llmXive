import os
import sys
from pathlib import Path

def main():
    """
    Creates the required directory structure for the project.
    Specifically targets code/ and tests/ directories as per T001c.
    Also ensures data/raw, data/processed, artifacts, and state exist
    to satisfy T001a and T001b which were previously rejected.
    """
    # Determine the project root based on the script location or a fixed relative path
    # Since the task asks for paths relative to the project root, we assume the script
    # is run from the project root or we define the root explicitly.
    # Given the constraint "Stay inside the project tree", we use relative paths.
    
    project_root = Path(".")
    
    # Directories required for T001c
    dirs_to_create = [
        project_root / "code",
        project_root / "tests",
        # Re-creating T001a and T001b directories to ensure full state compliance
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "artifacts",
        project_root / "state",
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
