import os
import sys
from pathlib import Path
from config import get_project_root

def create_directories():
    """
    Create the project directory structure as defined in T001a.
    Paths: data/raw/, data/processed/, code/, outputs/, tests/, state/projects/, code/models/
    """
    root = get_project_root()
    if not root:
        raise RuntimeError("Project root not found. Ensure CONFIG_ROOT is set or config.py is correctly configured.")

    root_path = Path(root)

    # Define relative paths to create
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "outputs",
        "tests",
        "state/projects",
        "code/models"
    ]

    created = []
    for dir_path in directories:
        full_path = root_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        else:
            # Ensure it is actually a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")

    return created

def main():
    """Entry point for directory creation."""
    print("Starting project directory creation...")
    try:
        created_dirs = create_directories()
        print(f"Successfully created directories:")
        for d in created_dirs:
            print(f"  - {d}")
        
        if not created_dirs:
            print("No new directories created (all already exist).")
        
        # Verify existence
        root_path = Path(get_project_root())
        missing = []
        for rel in ["data/raw", "data/processed", "code", "outputs", "tests", "state/projects", "code/models"]:
            if not (root_path / rel).exists():
                missing.append(rel)
        
        if missing:
            print(f"ERROR: The following directories are missing after creation attempt: {missing}")
            sys.exit(1)
        
        print("Verification complete: All required directories exist.")
    except Exception as e:
        print(f"ERROR: Failed to create directories: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
