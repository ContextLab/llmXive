import os
import sys
from pathlib import Path

# Define the required directory structure relative to the project root
REQUIRED_DIRS = [
    "code/data",
    "code/analysis",
    "code/reports",
    "code/utils",
    "code/tests",
    "data/raw",
    "data/processed",
    "data/consent"
]

def create_directories(base_path: Path) -> bool:
    """
    Creates all required directories under base_path.
    Returns True if all directories were created successfully.
    """
    success = True
    for dir_name in REQUIRED_DIRS:
        dir_path = base_path / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}")
            success = False
    return success

def verify_structure(base_path: Path) -> bool:
    """
    Verifies that all required directories exist and contain a .gitkeep file.
    Returns True if verification passes.
    """
    all_ok = True
    for dir_name in REQUIRED_DIRS:
        dir_path = base_path / dir_name
        gitkeep_path = dir_path / ".gitkeep"
        
        if not dir_path.exists():
            print(f"FAIL: Directory missing: {dir_path}")
            all_ok = False
            continue
        
        if not gitkeep_path.exists():
            print(f"FAIL: .gitkeep missing in {dir_path}, creating it...")
            try:
                gitkeep_path.touch()
                print(f"Created .gitkeep in {dir_path}")
            except OSError as e:
                print(f"FAIL: Could not create .gitkeep in {dir_path}: {e}")
                all_ok = False
        else:
            print(f"OK: {dir_path} exists with .gitkeep")
    
    return all_ok

def main():
    """
    Entry point for the project structure setup script.
    """
    # Determine project root (assumed to be the directory containing this script's parent)
    # Since this script is in code/, the root is two levels up from the script file location
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    print(f"Project root detected at: {project_root}")
    print("Starting directory creation and verification...")

    if not create_directories(project_root):
        print("Directory creation failed. Aborting verification.")
        sys.exit(1)

    if verify_structure(project_root):
        print("\nVerification successful: All required directories and .gitkeep files exist.")
        sys.exit(0)
    else:
        print("\nVerification failed: Some directories or .gitkeep files are missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()