import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure for PROJ-470-predicting-cognitive-fatigue-from-restin.
    This script ensures all required folders exist relative to the project root.
    """
    # Determine project root based on the current working directory or script location
    # Assuming the script is run from the project root
    project_root = Path.cwd()
    
    # Define the directory structure relative to project root
    # Note: The task description mentions 'projects/PROJ-470...' but the completed tasks
    # and execution context imply the structure should be at the root level (data/, code/, tests/)
    # to match the paths used in download.py, preprocess.py, etc.
    # We will create the specific project folder if it doesn't exist, but ensure the
    # standard pipeline directories (data, code, tests, docs) exist at the root
    # as referenced by the execution logs (e.g., 'data/raw', 'code/download.py').
    
    dirs_to_create = [
        "data/raw",
        "data/processed",
        "data/analysis",
        "code",
        "tests/unit",
        "tests/integration",
        "docs",
        # The specific project folder mentioned in T001 description
        "projects/PROJ-470-predicting-cognitive-fatigue-from-restin"
    ]
    
    created_count = 0
    existing_count = 0

    print(f"Setting up directory structure in: {project_root}")

    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            # Check if it's a directory, if it's a file, we might need to handle it differently
            # but for this task, we assume valid paths
            if full_path.is_dir():
                existing_count += 1
            else:
                print(f"Warning: Path exists but is not a directory: {full_path}")

    print(f"Setup complete. Created: {created_count}, Already existed: {existing_count}")
    
    # Verify the critical paths expected by the pipeline
    critical_paths = [
        "data/raw",
        "data/processed", 
        "code",
        "tests/unit",
        "tests/integration"
    ]
    
    missing = []
    for p in critical_paths:
        if not (project_root / p).exists():
            missing.append(p)
    
    if missing:
        print(f"ERROR: Critical directories missing after setup: {missing}")
        sys.exit(1)
    else:
        print("All critical directories verified.")

if __name__ == "__main__":
    main()