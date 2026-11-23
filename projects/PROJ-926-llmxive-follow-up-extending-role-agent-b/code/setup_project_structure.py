import os
import sys
from pathlib import Path

def create_project_structure():
    """
    Creates the full project directory structure as defined in tasks.md T001.
    Ensures src/, tests/, data/, state/, and docs/ exist with required subdirectories.
    """
    # Define the project root relative to where this script is run
    # We assume the script is run from the project root or the code/ directory
    # To be safe, we resolve relative to the script's location if needed,
    # but standard convention is to run from root.
    
    # If running from code/, we need to go up one level
    current_file = Path(__file__).resolve()
    if current_file.parent.name == 'code':
        project_root = current_file.parent
    else:
        project_root = current_file.parent.parent # Fallback if in subfolder
        
    # Actually, simpler: assume the script is executed from the project root 
    # or the 'code' folder, and we create paths relative to the current working directory
    # or the script's parent if we want to be strict.
    # Let's use the current working directory as the project root, 
    # but ensure we create the structure relative to where the script is 
    # if it's in a 'code' folder, we create the structure in the parent.
    
    # Re-evaluating based on "paths are relative to the project root"
    # If this script is at code/setup_project_structure.py, the project root is parent of code.
    base_dir = current_file.parent.parent
    
    directories = [
        "src/config",
        "src/sim",
        "src/retrieval",
        "src/conditions",
        "src/analysis",
        "src/data/raw",
        "src/data/derived",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "data/raw",
        "data/derived",
        "state",
        "docs"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        # Ensure existence even if they were there before
        if not full_path.exists():
            print(f"ERROR: Failed to create directory {full_path}")
            return False

    print(f"Project structure created successfully. {created_count} new directories created.")
    print(f"Base directory: {base_dir}")
    
    # Verify existence of critical paths
    required_paths = [
        "src", "tests", "data", "state", "docs",
        "src/config", "src/sim", "src/retrieval", "src/conditions", "src/analysis",
        "src/data/raw", "src/data/derived",
        "tests/contract", "tests/integration", "tests/unit",
        "data/raw", "data/derived"
    ]
    
    all_exist = True
    for p in required_paths:
        if not (base_dir / p).exists():
            print(f"VERIFICATION FAILED: {p} does not exist.")
            all_exist = False
    
    return all_exist

if __name__ == "__main__":
    success = create_project_structure()
    sys.exit(0 if success else 1)
