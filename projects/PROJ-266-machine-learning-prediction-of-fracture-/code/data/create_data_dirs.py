import os
import sys

def main():
    """
    Creates the required data directory structure for the project.
    
    Directories created:
    - data/
    - data/raw/
    - data/processed/
    - data/explainability/
    """
    base_dirs = [
        "data",
        "data/raw",
        "data/processed",
        "data/explainability"
    ]

    created_count = 0
    for dir_path in base_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"\nData directory setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())