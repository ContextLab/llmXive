import os
import sys
from pathlib import Path

def setup_directories():
    """
    Setup the data directory structure required for the project.
    Creates: data/raw, data/processed, data/splits, results.
    
    Verification: All directories exist after execution.
    """
    # Define the base directory relative to the script location
    # Assuming the script is run from the project root or code/ directory
    # We use the current working directory as the project root for safety
    project_root = Path.cwd()
    
    # Define the data directory paths
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/splits",
        "results"
    ]
    
    created_dirs = []
    skipped_dirs = []
    
    for dir_path in data_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            skipped_dirs.append(str(full_path))
            print(f"Directory already exists: {full_path}")
    
    # Verification step
    print("\n--- Verification ---")
    missing = []
    for dir_path in data_dirs:
        full_path = project_root / dir_path
        if not full_path.is_dir():
            missing.append(str(full_path))
    
    if missing:
        print(f"ERROR: The following directories are missing: {missing}")
        sys.exit(1)
    else:
        print("SUCCESS: All required data directories exist.")
        print(f"Contents of {project_root}/data/:")
        if (project_root / "data").exists():
            for item in (project_root / "data").iterdir():
                print(f"  - {item.name}")
        
        print(f"Contents of {project_root}/results/:")
        if (project_root / "results").exists():
            for item in (project_root / "results").iterdir():
                print(f"  - {item.name}")
        
        return True

if __name__ == "__main__":
    setup_directories()
