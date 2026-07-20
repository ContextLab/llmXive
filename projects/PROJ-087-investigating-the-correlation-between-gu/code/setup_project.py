import os
from pathlib import Path

def main():
    """
    Create the project directory structure and empty __init__.py files
    as specified in T001.
    """
    # Define the root directory for the project (current directory)
    root = Path(".")

    # Define the directories to create relative to root
    directories = [
        "src",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    # Define the locations for __init__.py files
    init_files = [
        "src/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py"
    ]

    # Create directories
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    # Create __init__.py files (empty)
    for file_path in init_files:
        full_path = root / file_path
        # Ensure parent directory exists before creating file
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if not full_path.exists():
            full_path.touch()
            print(f"Created file: {full_path}")
        else:
            print(f"File already exists: {full_path}")

    print("Project structure setup complete.")

if __name__ == "__main__":
    main()