import os
import sys
from pathlib import Path

def setup_code_directories():
    """
    Create the required subdirectories under the 'code/' directory.
    
    Directories to create:
    - code/
    - code/data/
    - code/models/
    - code/inference/
    - code/evaluation/
    - code/utils/
    - code/tasks/
    - code/tests/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    base_path = Path("code")
    subdirs = [
        "data",
        "models",
        "inference",
        "evaluation",
        "utils",
        "tasks",
        "tests"
    ]
    
    created_paths = []
    success = True
    
    # Ensure base 'code' directory exists
    base_path.mkdir(parents=True, exist_ok=True)
    created_paths.append(str(base_path))
    
    # Create subdirectories
    for subdir in subdirs:
        dir_path = base_path / subdir
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(dir_path))
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)
            success = False
    
    return success, created_paths

def main():
    """Main entry point for directory setup."""
    print("Setting up code directory structure...")
    success, created_paths = setup_code_directories()
    
    if success:
        print("Successfully created the following directories:")
        for path in created_paths:
            print(f"  - {path}")
        
        # Verification step as per task requirement
        print("\nVerifying directory creation...")
        all_verified = True
        for path in created_paths:
            if not os.path.isdir(path):
                print(f"  ❌ Verification failed for: {path}")
                all_verified = False
            else:
                print(f"  ✅ Verified: {path}")
        
        if all_verified:
            print("\n✅ All directories verified successfully.")
            return 0
        else:
            print("\n❌ Verification failed for some directories.")
            return 1
    else:
        print("\n❌ Failed to create some directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
