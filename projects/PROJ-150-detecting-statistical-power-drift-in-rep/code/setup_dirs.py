import os
import sys
from pathlib import Path

def main():
    """
    Creates the required directory structure for the project.
    Specifically creates: data/raw, data/derived, code, tests, results, state
    """
    project_root = Path.cwd()
    
    # Define the directories to create relative to the project root
    # Note: 'code' and 'tests' are often already present, but we ensure they exist.
    dirs_to_create = [
        "data/raw",
        "data/derived",
        "code",
        "tests",
        "results",
        "state"
    ]

    created_count = 0
    for dir_name in dirs_to_create:
        target_path = project_root / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {target_path}")
    
    print(f"Directory setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
