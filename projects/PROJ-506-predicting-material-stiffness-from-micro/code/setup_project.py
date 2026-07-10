import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure for PROJ-506.
    Verifies that all required directories exist after creation.
    """
    root = Path(__file__).parent.parent
    
    # Define the directory structure relative to the project root
    dirs_to_create = [
        # Code modules
        "code/data_generation",
        "code/training",
        "code/evaluation",
        "code/utils",
        
        # Data storage
        "data/raw",
        "data/processed",
        
        # Test suites
        "tests/unit",
        "tests/contract",
        "tests/integration",
        
        # Feature specs and contracts
        "specs/001-predict-stiffness-cnn/contracts",
    ]
    
    created_count = 0
    for dir_path in dirs_to_create:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory exists: {full_path}")
    
    print(f"\nTotal directories created: {created_count}")
    
    # Verification: Check that all directories actually exist
    all_exist = True
    for dir_path in dirs_to_create:
        full_path = root / dir_path
        if not full_path.is_dir():
            print(f"ERROR: Directory does not exist: {full_path}")
            all_exist = False
    
    if all_exist:
        print("\nVerification successful: All required directories exist.")
        return 0
    else:
        print("\nVerification failed: Some directories are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())