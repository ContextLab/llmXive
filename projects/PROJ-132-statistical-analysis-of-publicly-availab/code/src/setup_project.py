import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the required project directory structure for PROJ-132.
    This implements T002a: Create Project Structure.
    """
    # Define the root directory (project root)
    root = Path(__file__).resolve().parent.parent.parent

    # Define the directories to create relative to root
    directories = [
        "src/data",
        "src/models",
        "src/analysis",
        "src/utils",
        "src/cli",
        "data/raw",
        "data/processed",
        "data/interim",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    created_count = 0
    for dir_name in directories:
        target_path = root / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {target_path}")

    print(f"Project structure setup complete. {created_count} new directories created.")
    return True

def main():
    """Entry point for the setup script."""
    try:
        success = create_directories()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"Error during project structure creation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()