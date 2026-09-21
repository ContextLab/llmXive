import os
from pathlib import Path

def main():
    """
    Creates the required directory structure for the llmXive project.
    Directories created:
    - code/
    - data/raw/
    - data/processed/
    - data/results/
    - tests/
    """
    # Define the project root (current directory where script is run, or explicitly set)
    # Assuming script runs from project root as per standard llmXive conventions
    project_root = Path(".")
    
    # List of directories to create relative to project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests"
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
    
    print(f"Directory setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()