import os
from pathlib import Path

def main():
    """
    Creates the project directory structure as per the implementation plan.
    Directories created:
      - code/
      - data/raw
      - data/processed
      - data/models
      - tests/
      - tests/unit
      - tests/integration
    """
    # Define the project root (current working directory or explicit path if needed)
    # Assuming the script runs from the project root
    project_root = Path(".")

    # Define the directories to create
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/models",
        "tests",
        "tests/unit",
        "tests/integration",
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
            skipped_count += 1

    print(f"\nSetup complete. Created {created_count} new directories, skipped {skipped_count} existing.")

if __name__ == "__main__":
    main()