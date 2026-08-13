import os
import sys
from pathlib import Path

def setup_code_directories():
    """
    Create the required subdirectories under 'code/'.
    Returns a list of created paths.
    """
    base_path = Path(__file__).resolve().parent.parent
    code_dir = base_path / "code"
    
    subdirs = [
        "",  # code/ itself
        "data",
        "models",
        "inference",
        "evaluation",
        "utils",
        "tasks",
        "tests"
    ]
    
    created_paths = []
    
    for subdir in subdirs:
        target_path = code_dir / subdir
        os.makedirs(target_path, exist_ok=True)
        created_paths.append(target_path)
        print(f"Created directory: {target_path}")
        
    return created_paths

def verify_directories():
    """
    Verify that all required code subdirectories exist.
    Returns True if all exist, False otherwise.
    """
    base_path = Path(__file__).resolve().parent.parent
    code_dir = base_path / "code"
    
    subdirs = [
        "",
        "data",
        "models",
        "inference",
        "evaluation",
        "utils",
        "tasks",
        "tests"
    ]
    
    all_exist = True
    for subdir in subdirs:
        target_path = code_dir / subdir
        if not os.path.isdir(target_path):
            print(f"ERROR: Directory does not exist: {target_path}")
            all_exist = False
        else:
            print(f"Verified: {target_path}")
            
    return all_exist

def main():
    """
    Main entry point to create and verify code directories.
    """
    print("Setting up code directories...")
    created = setup_code_directories()
    print(f"\nCreated {len(created)} directories.")
    
    print("\nVerifying directories...")
    if verify_directories():
        print("\nAll required code directories exist.")
        return 0
    else:
        print("\nSome directories are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())