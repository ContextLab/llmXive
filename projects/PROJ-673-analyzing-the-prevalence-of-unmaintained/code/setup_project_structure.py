import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure as defined in T001.
    Ensures all required directories exist for the research pipeline.
    """
    # Define the project root (assuming code/ is the root for this task execution)
    # The paths are relative to where this script is run. 
    # Based on the task description, we create these under the project root.
    # We assume the script is run from the project root or code/ directory.
    # To be safe, we create them relative to the current working directory.
    root = Path.cwd()
    
    # Directories to create based on T001 description
    # Note: T001 mentions 'src/', 'tests/', 'data/', 'docs/'
    # The task note says: "Do NOT create contracts/ here"
    dirs_to_create = [
        "src/models",
        "src/services",
        "src/analysis",
        "src/cli",
        "src/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "docs"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in dirs_to_create:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            existing_count += 1
    
    print(f"Project structure setup complete.")
    print(f"  Created: {created_count} directories")
    print(f"  Existing: {existing_count} directories")
    
    # Verify creation
    missing = []
    for dir_path in dirs_to_create:
        if not (root / dir_path).exists():
            missing.append(dir_path)
    
    if missing:
        print(f"ERROR: Failed to create the following directories: {missing}")
        sys.exit(1)
    else:
        print("All required directories verified.")

if __name__ == "__main__":
    main()