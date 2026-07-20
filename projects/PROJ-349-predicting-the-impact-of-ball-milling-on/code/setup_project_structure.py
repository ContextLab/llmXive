import os
import sys
from pathlib import Path

def setup_directories():
    """
    Creates the project directory structure as defined in T001.
    
    Directories created:
    - src/
    - tests/
    - data/raw
    - data/processed
    - data/splits
    - results
    - contracts/
    - .github/workflows/
    
    Verification: All directories exist. Placeholder .gitkeep files are created
    in empty directories to ensure they are tracked by git.
    """
    # Define the project root (assuming this script is run from the root)
    project_root = Path(__file__).parent.parent
    
    # Define relative paths based on T001 requirements
    # Note: The task description mentions 'src/', 'tests/' at repository root.
    # The existing code structure uses 'code/' as the root for scripts.
    # We will create the structure relative to the current execution context 
    # but align with the project's intended layout.
    
    # Based on the "Existing project API surface", scripts are in 'code/'
    # and the project structure seems to be managed from there.
    # We will create the directories relative to the script's parent (code/)
    # to match the "code/code/..." pattern seen in the API surface, 
    # OR we assume the script is meant to be run from the repo root 
    # and create the standard structure.
    
    # Given the task says "Create project structure per implementation plan: 
    # src/, tests/, data/raw...", and the API surface shows files like 
    # code/setup_project_structure.py, we will create the directories 
    # relative to the repository root.
    # Assuming the script is executed from the repository root or 
    # the 'code' directory is the working directory.
    # Let's assume the script is run from the repo root to create the standard structure.
    # If running from 'code', we need to go up one level.
    
    base_path = Path(__file__).parent.parent if Path(__file__).parent.name == 'code' else Path(__file__).parent
    
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/splits",
        "results",
        "contracts",
        ".github/workflows"
    ]
    
    created_dirs = []
    for dir_path in directories:
        full_path = base_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            
            # Create .gitkeep in empty directories to ensure they are tracked
            # Check if directory is empty (only .gitkeep might be there)
            if not any(full_path.iterdir()):
                gitkeep_path = full_path / ".gitkeep"
                gitkeep_path.touch()
                
        except PermissionError:
            print(f"Permission denied: Unable to create {full_path}")
            return False
        except Exception as e:
            print(f"Error creating directory {full_path}: {e}")
            return False
    
    print(f"Successfully created {len(created_dirs)} directories.")
    for d in created_dirs:
        print(f"  - {d}")
    return True

if __name__ == "__main__":
    success = setup_directories()
    sys.exit(0 if success else 1)
