import os
from pathlib import Path

def main():
    """
    Creates the required directory structure for the PROJ-080 project.
    This function ensures the following directories exist relative to the project root:
    - data/raw
    - data/processed
    - code
    - tests/unit
    - tests/integration
    - specs/contracts
    """
    # Determine the project root. Since this script is run from the project root,
    # we use the current working directory.
    project_root = Path.cwd()
    
    # Define the relative paths to be created
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests/unit",
        "tests/integration",
        "specs/contracts"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    if created_count == 0:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {created_count} directory/directories.")

if __name__ == "__main__":
    main()