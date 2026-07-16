import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure for PROJ-470-predicting-cognitive-fatigue-from-restin.
    
    Creates the following directories relative to the project root:
    - projects/PROJ-470-predicting-cognitive-fatigue-from-restin/
    - data/raw/
    - data/processed/
    - data/analysis/
    - code/
    - tests/unit/
    - tests/integration/
    - docs/
    """
    # Define the project root. We assume the script is run from the project root
    # or that the current working directory is the project root.
    project_root = Path.cwd()
    
    # Define the base project directory as specified in the task
    base_project_dir = project_root / "projects" / "PROJ-470-predicting-cognitive-fatigue-from-restin"
    
    # Define subdirectories
    dirs_to_create = [
        base_project_dir,
        base_project_dir / "data" / "raw",
        base_project_dir / "data" / "processed",
        base_project_dir / "data" / "analysis",
        base_project_dir / "code",
        base_project_dir / "tests" / "unit",
        base_project_dir / "tests" / "integration",
        base_project_dir / "docs",
    ]
    
    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path.relative_to(project_root)}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path.relative_to(project_root)}")
    
    print(f"\nDirectory structure setup complete. Created {created_count} new directories.")
    print(f"Base project path: {base_project_dir.relative_to(project_root)}")
    
    # Verify structure
    print("\nVerifying directory structure:")
    all_exist = True
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            print(f"  ERROR: Missing {dir_path.relative_to(project_root)}")
            all_exist = False
        else:
            print(f"  OK: {dir_path.relative_to(project_root)}")
    
    if all_exist:
        print("\nAll required directories verified successfully.")
        return 0
    else:
        print("\nERROR: Some directories could not be created.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
