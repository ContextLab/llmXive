import os
import sys
from pathlib import Path

def main():
    """
    Initialize project directory structure.
    Creates code/, tests/, data/, and docs/ directories in the project root.
    """
    # Determine project root (parent of this script's directory)
    current_dir = Path(__file__).parent
    project_root = current_dir.parent

    directories = [
        "code",
        "tests",
        "data",
        "docs",
        # Subdirectories required by the pipeline specs
        "data/raw",
        "data/derived",
        "data/interim",
        "figures",
        "contracts",
        "specs",
    ]

    created = []
    skipped = []

    for dir_name in directories:
        target_path = project_root / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            created.append(str(target_path.relative_to(project_root)))
        else:
            skipped.append(str(target_path.relative_to(project_root)))

    print(f"Project Root: {project_root}")
    print(f"Directories created: {created}")
    if skipped:
        print(f"Directories already existing: {skipped}")

    # Verify structure
    required_root_dirs = ["code", "tests", "data", "docs"]
    missing = [d for d in required_root_dirs if not (project_root / d).exists()]
    if missing:
        print(f"ERROR: Missing required root directories: {missing}")
        sys.exit(1)
    
    print("Directory structure initialization complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
