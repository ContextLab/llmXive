import os
from pathlib import Path

def main():
    """
    Create the required project directory structure.
    Implements T001a: Create code/, data/raw/, data/processed/, data/results/, tests/ directories.
    """
    base_path = Path.cwd()
    
    # Define directories relative to project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    if created_count > 0:
        print(f"Successfully created {created_count} new directories.")
    else:
        print("All directories already existed.")
    
    # Verify creation
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.is_dir():
            raise RuntimeError(f"Failed to create directory: {dir_path}")
    
    print("Directory structure verification complete.")

if __name__ == "__main__":
    main()