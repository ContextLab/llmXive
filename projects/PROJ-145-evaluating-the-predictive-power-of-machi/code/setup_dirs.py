import os
from pathlib import Path

def main():
    """
    Create the root directory structure for the project.
    This script ensures the existence of code/, data/raw/, data/processed/,
    data/models/, tests/unit/, tests/integration/, and specs/ directories.
    """
    # Define the root directory (project root)
    root = Path(__file__).resolve().parent.parent

    # Define the required directories relative to the root
    dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/models",
        "tests/unit",
        "tests/integration",
        "specs"
    ]

    created_count = 0
    for dir_name in dirs:
        dir_path = root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Directory setup complete. Created {created_count} new directories.")

if __name__ == "__main__":
    main()
