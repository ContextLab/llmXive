import os
import sys
from pathlib import Path

def setup_directories():
    """
    Create the project directory structure as defined in T001.
    Directories created relative to the project root (code/).
    """
    # Define the base directory (project root)
    # Assuming this script runs from the project root or 'code' folder
    # We will create directories relative to the current working directory
    base_dir = Path.cwd()

    # Define required directories per T001
    # Note: The task asks for 'src/', 'tests/', etc. at repository root.
    # Since we are in 'code/', we create them here to simulate the structure
    # or we assume the project root is the parent.
    # Based on the prompt's path conventions and existing files in 'code/',
    # we will create the structure inside the current directory (which acts as the root for this task).
    
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/splits",
        "results",
        "contracts",
        ".github/workflows"
    ]

    created_count = 0
    for dir_name in directories:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Setup complete. Created {created_count} new directories.")
    return True

if __name__ == "__main__":
    setup_directories()
