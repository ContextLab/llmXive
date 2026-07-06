import os
from pathlib import Path

def main():
    """
    Setup the required directory structure for the project.
    Creates:
      - data/raw/
      - data/processed/
      - docs/figures/
      - state/projects/
    """
    # Define the project root based on the current working directory structure
    # Assuming this script is run from the project root or code/ directory
    # We need to locate the project root which contains 'data', 'docs', 'state'
    
    # Determine the base path (project root)
    # If running from code/, go up one level
    current_path = Path(__file__).resolve()
    if current_path.name == 'setup_directories.py':
        # We are in code/
        base_path = current_path.parent
    else:
        base_path = current_path.parent.parent

    # Ensure we are at the project root (check for existence of 'code' folder)
    # If 'code' is not a sibling, assume base_path is the root
    if not (base_path / 'code').exists():
        base_path = base_path.parent

    # Define directories to create
    directories = [
        base_path / 'data' / 'raw',
        base_path / 'data' / 'processed',
        base_path / 'docs' / 'figures',
        base_path / 'state' / 'projects'
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    exit(main())