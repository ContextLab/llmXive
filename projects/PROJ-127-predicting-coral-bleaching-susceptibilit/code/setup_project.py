import os
from pathlib import Path

def main():
    """
    Create the project directory structure as per the implementation plan.
    Directories: code/, data/raw, data/processed, data/models, tests/
    """
    # Define the project root (current directory)
    root = Path(".")

    # Define required directories relative to root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/models",
        "tests",
        "tests/unit",
        "tests/integration",
        "specs",
        "figures",
    ]

    created_count = 0
    for dir_name in directories:
        dir_path = root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"\nProject structure setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()
