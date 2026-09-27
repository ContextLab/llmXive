import os
import sys
from pathlib import Path

def main():
    """
    Creates the required directory structure for the project.
    Specifically creates 'code' and 'tests' directories under the project root.
    Also ensures 'data/raw', 'data/processed', 'artifacts', and 'state' exist
    to satisfy T001a and T001b requirements which were previously rejected.
    """
    # Determine project root based on the script location or environment
    # The task specifies paths relative to project root:
    # projects/PROJ-712-predicting-individual-pain-sensitivity-f/
    
    # We assume the script is run from the repository root or the project root
    # Let's define the project root explicitly to match the task requirement
    # Since the task asks to create directories under "projects/PROJ-712..."
    # we will create that structure relative to the current working directory.
    
    base_dir = Path.cwd()
    project_root = base_dir / "projects" / "PROJ-712-predicting-individual-pain-sensitivity-f"
    
    directories = [
        project_root / "code",
        project_root / "tests",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "artifacts",
        project_root / "state"
    ]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
