import os
import sys
from pathlib import Path

def create_t001b_directories():
    """
    Creates the directory structure for Task T001b.
    This includes src/, tests/, data/ and their specific subdirectories.
    """
    # Determine project root based on the current file location
    # Assuming this script is run from code/ or code/ is the root
    current_dir = Path(__file__).parent
    project_root = current_dir.parent / "projects" / "PROJ-951-llmxive-follow-up-extending-physisforcin"
    
    # Ensure the project root exists
    project_root.mkdir(parents=True, exist_ok=True)
    
    # Define the base directories relative to project root
    base_dirs = [
        "src",
        "tests",
        "data"
    ]
    
    # Define specific subdirectories
    src_subdirs = [
        "src/generation",
        "src/filtering",
        "src/training",
        "src/evaluation",
        "src/utils"
    ]
    
    tests_subdirs = [
        "tests/unit",
        "tests/integration"
    ]
    
    data_subdirs = [
        "data/raw",
        "data/curated",
        "data/eval",
        "data/validation"
    ]
    
    # Combine all directories to create
    all_dirs = [
        Path(project_root) / d for d in base_dirs
    ] + [
        Path(project_root) / d for d in src_subdirs
    ] + [
        Path(project_root) / d for d in tests_subdirs
    ] + [
        Path(project_root) / d for d in data_subdirs
    ]
    
    created_count = 0
    for dir_path in all_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nTask T001b complete. Created {created_count} new directories.")
    print(f"Project root: {project_root}")
    
    # Verify structure
    print("\nVerifying structure...")
    missing = []
    for dir_path in all_dirs:
        if not dir_path.is_dir():
            missing.append(str(dir_path))
    
    if missing:
        print(f"ERROR: The following directories are missing: {missing}")
        sys.exit(1)
    else:
        print("All required directories verified successfully.")

if __name__ == "__main__":
    create_t001b_directories()