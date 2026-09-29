import os
from pathlib import Path

def main():
    """
    Create the required directory structure for the project.
    Implements Task T008: Create data/raw, data/processed, data/spot_check, artifacts, tests.
    """
    # Define the project root relative to where the script is run or standard project root
    # Assuming the script runs from the project root or we define it explicitly
    project_root = Path(__file__).resolve().parent.parent

    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "spot_check",
        project_root / "artifacts",
        project_root / "tests",
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    if created_count == 0:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {created_count} new directory(ies).")

if __name__ == "__main__":
    main()