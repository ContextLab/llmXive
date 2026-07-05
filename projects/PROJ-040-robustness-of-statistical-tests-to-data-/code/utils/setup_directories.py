import os
from pathlib import Path

def main():
    """
    Create the project directory structure for PROJ-040.
    This script ensures all required folders exist relative to the project root.
    """
    # Determine project root. Since this script is in code/utils/,
    # we assume the project root is two levels up (../../).
    # However, to be robust, we can also look for the specific project folder name
    # or assume the script is run from the project root.
    # Based on the task description, the structure is inside:
    # projects/PROJ-040-robustness-of-statistical-tests-to-data-/
    
    # We will construct the paths relative to the current file's location
    # to ensure they are created in the correct nested structure if this
    # file is moved, or relative to the current working directory if run directly.
    
    # The task explicitly lists the target path:
    # projects/PROJ-040-robustness-of-statistical-tests-to-data-/...
    
    # Let's assume the script is run from the repository root.
    # If the script is part of a larger project where the root is defined differently,
    # we will use the path provided in the task description as the base.
    
    base_path = Path("projects/PROJ-040-robustness-of-statistical-tests-to-data-")
    
    directories = [
        "code/data",
        "code/utils",
        "code/viz",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "docs"
    ]
    
    created_count = 0
    for dir_name in directories:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    exit(main())
