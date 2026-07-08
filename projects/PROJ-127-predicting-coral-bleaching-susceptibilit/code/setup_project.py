import os
from pathlib import Path

def main():
    """
    Creates the project directory structure for the Coral Bleaching Susceptibility project.
    Creates:
      - code/
      - data/raw
      - data/processed
      - data/models
      - tests/
    """
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/models",
        "tests"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()
