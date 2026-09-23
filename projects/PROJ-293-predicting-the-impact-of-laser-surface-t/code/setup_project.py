import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure as defined in the implementation plan.
    Creates: code/, data/, tests/, state/, reports/, models/, data/raw/, data/processed/
    """
    base_dir = Path(".")
    
    directories = [
        "code",
        "data",
        "tests",
        "state",
        "reports",
        "models",
        "data/raw",
        "data/processed"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_name in directories:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
            existing_count += 1
    
    print(f"Project structure setup complete. Created: {created_count}, Existing: {existing_count}")
    
    # Verify all directories exist
    all_exist = all((base_dir / d).exists() and (base_dir / d).is_dir() for d in directories)
    if not all_exist:
        print("ERROR: Some directories failed to create or verify.")
        sys.exit(1)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
