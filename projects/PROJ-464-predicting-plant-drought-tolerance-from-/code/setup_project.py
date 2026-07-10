import os
from pathlib import Path

def main():
    """
    T001a: Create project directories.
    Creates the following directories relative to the project root:
    data/raw/, data/derived/, code/, tests/, docs/, state/, contracts/, results/
    """
    # Define the base directory (project root)
    base_dir = Path.cwd()
    
    # Define the relative paths to be created
    directories = [
        "data/raw",
        "data/derived",
        "code",
        "tests",
        "docs",
        "state",
        "contracts",
        "results"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Setup complete. {created_count} new directory(ies) created.")
    return 0

if __name__ == "__main__":
    exit(main())
