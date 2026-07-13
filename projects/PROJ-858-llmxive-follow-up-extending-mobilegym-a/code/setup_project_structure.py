import os
import sys

# Define the required directory structure based on the project plan
DIRECTORIES = [
    "code",
    "code/scheduler",
    "code/training",
    "code/analysis",
    "code/utils",
    "data/raw",
    "data/processed",
    "data/validation",
    "tests/unit",
    "tests/integration",
    "contracts",
]

def create_directory(path: str) -> bool:
    """Create a directory if it does not exist."""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main() -> int:
    """Main entry point to create the project structure."""
    print("Creating project directory structure...")
    success = True
    for dir_path in DIRECTORIES:
        if create_directory(dir_path):
            print(f"  Created: {dir_path}")
        else:
            success = False
            print(f"  Failed: {dir_path}")

    if success:
        print("Project structure created successfully.")
        return 0
    else:
        print("Some directories failed to create.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
