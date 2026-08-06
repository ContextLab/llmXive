import os
import sys
from pathlib import Path

def main():
    """
    Create the required data and artifact directory structure for the project.
    Implements Task T004.
    """
    # Determine the project root. Since this script is in code/, we go up one level.
    # However, the task description implies a specific project root structure.
    # Based on T001/T001b context, the root is the current directory where the script is run,
    # or we assume the script is run from the project root.
    # To be safe and robust, we assume the script is run from the project root.
    project_root = Path.cwd()

    # Define the required directories relative to the project root
    directories = [
        "data/raw",
        "data/processed",
        "artifacts/figures",
        "artifacts/logs"
    ]

    created_count = 0
    existing_count = 0

    for dir_path in directories:
        full_path = project_root / dir_path
        if full_path.exists():
            if full_path.is_dir():
                print(f"Directory '{dir_path}' already exists.")
                existing_count += 1
            else:
                print(f"Error: '{dir_path}' exists but is not a directory.")
                sys.exit(1)
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: '{dir_path}'")
            created_count += 1

    print(f"\nDirectory setup complete. Created: {created_count}, Existing: {existing_count}")

if __name__ == "__main__":
    main()