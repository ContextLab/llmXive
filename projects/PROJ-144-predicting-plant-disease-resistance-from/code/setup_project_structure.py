import os
import sys
from pathlib import Path

def create_structure():
    """
    Creates the project directory structure as defined in the implementation plan.
    Directories created:
    - code/
    - data/raw
    - data/processed
    - tests/
    - state/
    - results/
    - contracts/
    """
    base_dir = Path(".")
    
    # Define the required directories relative to the project root
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "state",
        "results",
        "contracts"
    ]
    
    created_count = 0
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nProject structure verification complete.")
    print(f"Total directories checked: {len(required_dirs)}")
    print(f"New directories created: {created_count}")
    
    # Verify all exist
    all_exist = all((base_dir / d).exists() for d in required_dirs)
    if all_exist:
        print("SUCCESS: All required directories exist.")
        return True
    else:
        print("FAILURE: Some directories are missing.")
        return False

if __name__ == "__main__":
    success = create_structure()
    sys.exit(0 if success else 1)
