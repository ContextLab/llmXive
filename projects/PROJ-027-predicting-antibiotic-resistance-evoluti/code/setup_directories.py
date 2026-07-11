import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the required directory structure for the llmXive research pipeline.
    Returns a list of created paths.
    """
    base_dir = Path(__file__).resolve().parent.parent
    code_dir = base_dir / "code"
    
    # Define the directories to create as per task T001a
    directories = [
        code_dir / "01_ingest",
        code_dir / "02_process",
        code_dir / "03_model",
        code_dir / "04_validate",
        code_dir / "05_viz",
    ]
    
    created_paths = []
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(dir_path)
        print(f"Created directory: {dir_path.relative_to(base_dir)}")
        
    return created_paths

def verify_directories():
    """
    Verify that all required directories exist.
    Returns True if all exist, False otherwise.
    """
    base_dir = Path(__file__).resolve().parent.parent
    code_dir = base_dir / "code"
    
    required_dirs = [
        "01_ingest",
        "02_process",
        "03_model",
        "04_validate",
        "05_viz",
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = code_dir / dir_name
        if not dir_path.is_dir():
            print(f"ERROR: Directory missing: {dir_path.relative_to(base_dir)}")
            all_exist = False
        else:
            print(f"Verified: {dir_path.relative_to(base_dir)}")
    
    return all_exist

def main():
    """
    Entry point to create and verify directories.
    """
    print("=== llmXive Directory Setup (Task T001a) ===")
    create_directories()
    print("\n--- Verification ---")
    if verify_directories():
        print("All required directories exist.")
        return 0
    else:
        print("Verification failed: Some directories are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())