import os
from pathlib import Path

def setup_directories():
    """
    Create the required directory structure for the project.
    Creates: code/, data/, data/raw/, data/processed/, data/analysis/,
             tests/, contracts/, state/
    """
    # Define the project root relative to this file's location or current working dir
    # Assuming this script runs from the project root or we define paths relative to it.
    # We will use the current working directory as the project root.
    project_root = Path.cwd()

    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/analysis",
        "tests",
        "contracts",
        "state"
    ]

    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    if created_count == 0:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {created_count} new directories.")

if __name__ == "__main__":
    setup_directories()