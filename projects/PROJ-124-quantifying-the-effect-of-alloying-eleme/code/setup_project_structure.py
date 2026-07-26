import os
import sys
from pathlib import Path

def create_project_structure():
    """
    Initialize the project directory structure as defined in T001.
    Creates directories for code, data, state, output, tests, and docs.
    """
    # Define the directory structure relative to the project root
    # The script assumes it is run from the project root or the project root is passed as an argument
    base_path = Path(".")
    
    directories = [
        "code/data",
        "code/models",
        "code/utils",
        "code/config",
        "data/raw",
        "data/processed",
        "data/config", # Added for elements.yaml as referenced in T008b/T030
        "state",
        "output",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "docs/paper",
        "docs/reports",
        "logs", # Added for logger output as referenced in T006a
        "figures" # Added for potential plot outputs
    ]

    created_dirs = []
    skipped_dirs = []

    for dir_path in directories:
        full_path = base_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            # Verify writability by attempting a touch (create empty file)
            test_file = full_path / ".gitkeep"
            test_file.touch(exist_ok=True)
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
            skipped_dirs.append(str(full_path))

    # Verification step as per T001
    required_roots = ["code", "data", "state", "output", "tests", "docs"]
    missing_roots = []
    
    for root in required_roots:
        if not (base_path / root).exists():
            missing_roots.append(root)

    if missing_roots:
        print(f"CRITICAL: Missing required root directories: {missing_roots}", file=sys.stderr)
        return False

    print("Project structure initialized successfully.")
    print(f"Created {len(created_dirs)} directories.")
    if skipped_dirs:
        print(f"Skipped/Failed {len(skipped_dirs)} directories: {skipped_dirs}")
    
    return True

def main():
    success = create_project_structure()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()