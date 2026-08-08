import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure as defined in FR-001.
    Executes the equivalent of:
    mkdir -p code/ code/utils/ tests/ data/raw data/processed data/synthetic models/ docs/ docs/contracts/ state/projects/
    """
    project_root = Path.cwd()
    
    # Define the required directories relative to the project root
    dirs_to_create = [
        "code",
        "code/utils",
        "tests",
        "data/raw",
        "data/processed",
        "data/synthetic",
        "models",
        "docs",
        "docs/contracts",
        "state/projects",
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            # Even if it exists, ensure it is a directory
            if full_path.is_dir():
                print(f"Directory exists: {full_path}")
            else:
                print(f"ERROR: Path exists but is not a directory: {full_path}", file=sys.stderr)
                sys.exit(1)

    if created_count > 0:
        print(f"Successfully created {created_count} new directories.")
    else:
        print("All required directories already exist.")

    # Verify the structure exists as a final check
    missing = []
    for dir_path in dirs_to_create:
        if not (project_root / dir_path).is_dir():
            missing.append(dir_path)
    
    if missing:
        print(f"ERROR: The following directories are missing after creation attempt: {missing}", file=sys.stderr)
        sys.exit(1)
    
    print("Project structure verification passed.")

if __name__ == "__main__":
    main()
