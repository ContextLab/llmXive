import os
import sys
from pathlib import Path

def main():
    """
    Initialize the project directory structure for PROJ-181-predicting-species-distribution-shifts-u.
    Creates all required subdirectories under the project root.
    """
    # Determine project root based on script location or current working directory
    # Assuming this script is run from the project root or the script is located in code/
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    project_name = "PROJ-181-predicting-species-distribution-shifts-u"
    project_path = project_root / "projects" / project_name
    
    # Define required subdirectories relative to project_path
    subdirs = [
        "code",
        "data",
        "tests",
        "metrics",
        "reports",
        "logs",
        "state",
        "data/raw",
        "data/processed",
        "data/artifacts",
        "tests/unit",
        "tests/integration",
        "contracts"
    ]
    
    created_dirs = []
    for subdir in subdirs:
        full_path = project_path / subdir
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
            return 1
    
    print(f"Successfully created project structure at: {project_path}")
    print(f"Created {len(created_dirs)} subdirectories:")
    for d in created_dirs:
        print(f"  - {d}")
        
    return 0

if __name__ == "__main__":
    sys.exit(main())