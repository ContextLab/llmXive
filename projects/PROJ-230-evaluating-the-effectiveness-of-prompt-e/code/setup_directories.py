import os
import sys

def create_directories():
    """
    Creates the required directory structure for the project.
    Directories created relative to the project root:
    - src/
    - tests/
    - data/
    - data/raw/
    - data/processed/
    - data/prompts/
    - data/evaluation/
    - state/
    - state/checksums/
    """
    # Define the base directory (project root)
    # We assume the script is run from the project root or the script
    # determines the root based on its location.
    # For robustness, we use the directory where this script resides as the root.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(base_dir) == 'code':
        project_root = os.path.dirname(base_dir)
    else:
        project_root = base_dir

    directories = [
        "src",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/prompts",
        "data/evaluation",
        "state",
        "state/checksums"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = os.path.join(project_root, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    create_directories()