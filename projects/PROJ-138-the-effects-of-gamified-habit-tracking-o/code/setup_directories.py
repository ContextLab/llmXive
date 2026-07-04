import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required directory structure for the llmXive project.
    Ensures all specified directories exist and creates .gitkeep files
    to ensure they are tracked by git.
    """
    # Define the project root (assuming the script is run from the repo root)
    # If run from code/, we need to adjust. We assume execution from root.
    project_root = Path(".")
    
    directories = [
        "data/raw",
        "data/processed",
        "data/consent",
        "code/data",
        "code/analysis",
        "code/reports",
        "code/utils",
        "code/tests"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
        
        # Create .gitkeep to ensure directory is tracked
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in: {dir_path}")
        else:
            print(f".gitkeep already exists in: {dir_path}")

    print(f"\nDirectory setup complete. {created_count} new directories created.")
    return True

def verify_structure():
    """
    Verifies that all required directories and .gitkeep files exist.
    Returns True if all checks pass, False otherwise.
    """
    project_root = Path(".")
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/consent",
        "code/data",
        "code/analysis",
        "code/reports",
        "code/utils",
        "code/tests"
    ]
    
    all_ok = True
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.is_dir():
            print(f"ERROR: Directory missing: {dir_path}")
            all_ok = False
            continue
        
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            print(f"ERROR: .gitkeep missing in: {dir_path}")
            all_ok = False
    
    if all_ok:
        print("Verification successful: All directories and .gitkeep files exist.")
    return all_ok

def main():
    """
    Entry point for the directory setup script.
    Creates directories, verifies structure, and exits with appropriate code.
    """
    print("Starting directory setup...")
    create_directories()
    
    if verify_structure():
        print("Setup completed successfully.")
        sys.exit(0)
    else:
        print("Setup completed with errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()