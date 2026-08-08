import os
import sys
from pathlib import Path

def main():
    """
    Creates the root project directory structure for PROJ-951-llmxive-follow-up-extending-physisforcin.
    This implements Task T001: Create project root directories.
    
    Target Path: projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/
    """
    # Define the project root relative to the current working directory
    # Assuming the script is run from the project root or code directory
    current_dir = Path.cwd()
    
    # Determine the base path for the project
    # If run from code/, go up one level
    if current_dir.name == 'code':
        base_path = current_dir.parent
    else:
        base_path = current_dir
        
    project_root = base_path / 'projects' / 'PROJ-951-llmxive-follow-up-extending-physisforcin'
    code_root = project_root / 'code'
    
    print(f"Creating project root at: {project_root}")
    print(f"Creating code directory at: {code_root}")
    
    # Create directories
    project_root.mkdir(parents=True, exist_ok=True)
    code_root.mkdir(parents=True, exist_ok=True)
    
    print(f"Successfully created directories.")
    print(f"Project Root: {project_root}")
    print(f"Code Root: {code_root}")
    
    # Verify creation
    if project_root.exists() and code_root.exists():
        print("Verification: Directories exist.")
        return 0
    else:
        print("Verification: FAILED - Directories missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
