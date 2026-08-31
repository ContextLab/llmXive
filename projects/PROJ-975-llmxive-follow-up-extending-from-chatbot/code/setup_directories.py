import os
import sys

def create_project_structure():
    """
    Creates the required subdirectories for the llmXive project.
    Does NOT create the root project directory itself, only subdirectories.
    """
    base_dirs = [
        "data/raw",
        "data/results",
        "code",
        "tests/unit",
        "tests/contract",
        "contracts",
    ]

    created_count = 0
    for dir_path in base_dirs:
        if not os.path.exists(dir_path):
          os.makedirs(dir_path, exist_ok=True)
          print(f"Created directory: {dir_path}")
          created_count += 1
        else:
          print(f"Directory already exists: {dir_path}")

    return created_count

def main():
    """Entry point for directory setup."""
    print("Setting up project directory structure...")
    count = create_project_structure()
    print(f"Setup complete. Created {count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
