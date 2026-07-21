import os
from pathlib import Path
from config import get_project_root

def create_directories():
    """
    Creates the standard project directory structure required by the implementation plan.
    Directories created:
      - code/
      - data/raw/
      - data/processed/
      - data/consent/
      - tests/
      - tests/unit/
      - tests/integration/
      - tests/contract/
      - specs/
      - specs/001-text-tone-emotional-support/
      - specs/001-text-tone-emotional-support/contracts/
    """
    root = get_project_root()
    
    # Define all required directories relative to the project root
    # Using Path objects for cross-platform compatibility
    dirs_to_create = [
        "code",
        "data/raw",
        "data/processed",
        "data/consent",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "specs",
        "specs/001-text-tone-emotional-support",
        "specs/001-text-tone-emotional-support/contracts",
        "figures"
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            # Ensure it is actually a directory
            if full_path.is_dir():
                print(f"Directory exists: {full_path}")
            else:
                raise FileExistsError(f"Path exists but is not a directory: {full_path}")

    print(f"Project structure setup complete. {created_count} new directories created.")
    return True

def main():
    """Entry point for script execution."""
    try:
        create_directories()
        print("Success: Project structure verified.")
        return 0
    except Exception as e:
        print(f"Error: Failed to create project structure: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
