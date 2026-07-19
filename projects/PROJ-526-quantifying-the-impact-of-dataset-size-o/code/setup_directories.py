import os
from pathlib import Path

def create_directories():
    """
    Creates the required directory structure for the project.
    Ensures existence of data/raw, data/processed, state, and other standard folders.
    """
    # Define the project root relative to this file's location or the current working directory
    # Assuming the script is run from the project root or code/ directory, we resolve relative to cwd
    project_root = Path.cwd()

    # Define the directory structure to create
    directories = [
        "data/raw",
        "data/processed",
        "state",
        "docs",
        "tests/contract",
        "tests/unit",
        "tests/integration",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        # Ensure permissions are correct (optional, but good practice)
        # os.chmod(full_path, 0o755)

    return created_count

def main():
    """Entry point for directory creation."""
    print("Creating project directory structure...")
    count = create_directories()
    print(f"Successfully created {count} new directories.")
    print("Directory structure ready.")

if __name__ == "__main__":
    main()
