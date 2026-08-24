import os
import sys
from pathlib import Path

def main():
    """
    Initialize the project directory structure for PROJ-809-llmxive-follow-up-extending-a-stylometri.
    
    Creates the following hierarchy relative to the project root:
    - code/
    - data/
      - raw/
      - processed/
      - hybrid/
    - artifacts/
      - models/
      - metrics/
    - contracts/
    - tests/
      - unit/
      - contract/
      - integration/
    - state/
    """
    # Determine project root. We assume the script is run from the repository root.
    # If run from a subdirectory, we look for the specific project folder or assume CWD is root.
    # Based on task description, we are creating structure inside:
    # projects/PROJ-809-llmxive-follow-up-extending-a-stylometri/
    # However, the existing API surface shows files like `code/config.py` at the root of the context.
    # The task specifically says: "Initialize project directory structure (projects/PROJ-809-llmxive-follow-up-extending-a-stylometri/)"
    # But the existing files (code/utils.py, etc.) imply a flat structure or a specific root.
    # Let's assume the current working directory IS the project root for the structure to be created.
    # The task description mentions the path `projects/...` as the target, but the existing files
    # (e.g., code/setup_project.py) suggest we are already in the project root or a workspace.
    # To be safe and consistent with the "Extend, don't re-author" constraint and the existing file paths
    # provided in the API surface (e.g. `code/utils.py`), we will create the structure relative to CWD.
    # If the user intends to run this inside a `projects/...` folder, CWD should be that folder.
    
    root = Path.cwd()
    
    # Define the directory tree to create
    # Based on task T001 description:
    # code/, data/ (raw, processed, hybrid), artifacts/ (models, metrics), contracts/,
    # tests/ (unit, contract, integration), state/
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/hybrid",
        "artifacts/models",
        "artifacts/metrics",
        "contracts",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "state"
    ]
    
    created_count = 0
    existing_count = 0
    
    print(f"Initializing project structure at: {root}")
    
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            existing_count += 1
            
    print(f"Project initialization complete. Created {created_count} directories, {existing_count} already existed.")
    
    # Create .gitkeep files to ensure directories are tracked by git if needed
    # This is a common practice for empty directories
    for dir_path in directories:
        full_path = root / dir_path
        keep_file = full_path / ".gitkeep"
        if not keep_file.exists():
            keep_file.write_text("")
            
    return 0

if __name__ == "__main__":
    sys.exit(main())