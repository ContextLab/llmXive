import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required directory structure for the llmXive research pipeline.
    
    Directories created:
    - data/raw, data/processed, data/consent
    - code/data, code/analysis, code/reports, code/utils, code/tests
    """
    # Define the project root (parent of the 'code' directory where this script lives)
    # Assuming this script is at code/setup_directories.py
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Define relative paths to create
    dirs_to_create = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "consent",
        project_root / "code" / "data",
        project_root / "code" / "analysis",
        project_root / "code" / "reports",
        project_root / "code" / "utils",
        project_root / "code" / "tests",
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path.relative_to(project_root)}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path.relative_to(project_root)}")
    
    print(f"Total directories created: {created_count}")
    return created_count

def verify_structure():
    """
    Verifies that all required directories exist and creates .gitkeep files.
    """
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    dirs_to_check = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "consent",
        project_root / "code" / "data",
        project_root / "code" / "analysis",
        project_root / "code" / "reports",
        project_root / "code" / "utils",
        project_root / "code" / "tests",
    ]

    all_good = True
    for dir_path in dirs_to_check:
        if not dir_path.exists() or not dir_path.is_dir():
            print(f"ERROR: Missing directory: {dir_path.relative_to(project_root)}")
            all_good = False
        else:
            # Ensure .gitkeep exists
            gitkeep = dir_path / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
                print(f"Created .gitkeep in: {dir_path.relative_to(project_root)}")
            else:
                print(f".gitkeep exists in: {dir_path.relative_to(project_root)}")

    return all_good

def main():
    """
    Main entry point for the directory setup script.
    """
    print("Starting directory structure setup...")
    create_directories()
    if verify_structure():
        print("Directory structure verification: PASSED")
        sys.exit(0)
    else:
        print("Directory structure verification: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()