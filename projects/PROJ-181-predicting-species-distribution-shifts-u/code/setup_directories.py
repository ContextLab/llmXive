import os
import sys
from pathlib import Path

# Define the project root relative to this script's location or current working directory
# The tasks.md specifies paths relative to the project root.
# We will assume the script is run from the project root or the paths are absolute relative to CWD.
# Based on T001a description: "Create `projects/PROJ-181-predicting-species-distribution-shifts-u/data/`..."
# This implies the project structure might be nested inside a `projects` folder.

PROJECT_NAME = "PROJ-181-predicting-species-distribution-shifts-u"
PROJECTS_ROOT = Path("projects")
PROJECT_ROOT = PROJECTS_ROOT / PROJECT_NAME

# Data directories as specified in T001a
DATA_DIRS = [
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "data" / "raw",
    PROJECT_ROOT / "data" / "processed",
    PROJECT_ROOT / "data" / "artifacts",
]

def main():
    """
    Initialize the project directory structure for Data (T001a).
    Creates:
      - projects/PROJ-181-predicting-species-distribution-shifts-u/data/
      - projects/PROJ-181-predicting-species-distribution-shifts-u/data/raw/
      - projects/PROJ-181-predicting-species-distribution-shifts-u/data/processed/
      - projects/PROJ-181-predicting-species-distribution-shifts-u/data/artifacts/
    """
    print(f"Initializing data directory structure for project: {PROJECT_NAME}...")
    
    created_count = 0
    for dir_path in DATA_DIRS:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {dir_path}")
            created_count += 1
        else:
            print(f"Exists: {dir_path}")
    
    print(f"Directory initialization complete. {created_count} new directories created.")
    
    # Verification step to ensure paths exist
    all_exist = all(d.exists() and d.is_dir() for d in DATA_DIRS)
    if not all_exist:
        print("ERROR: Some directories failed to create.", file=sys.stderr)
        sys.exit(1)
    
    # List the created structure for verification
    print("\nCurrent Data Directory Structure:")
    for d in DATA_DIRS:
        # Print relative to project root for cleaner output
        rel_path = d.relative_to(PROJECT_ROOT)
        print(f"  - {rel_path}")

if __name__ == "__main__":
    main()