import os
import sys
from pathlib import Path

def create_t001b_directories(base_path: Path) -> bool:
    """
    Creates the src/, tests/, and data/ subdirectories under the project code root.
    
    Args:
        base_path: The project root directory (projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/)
        
    Returns:
        True if all directories were created successfully, False otherwise.
    """
    directories = [
        "src",
        "tests",
        "data"
    ]
    
    success = True
    for dir_name in directories:
        dir_path = base_path / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}")
            success = False
            
    return success

def main():
    """Main entry point for T001b directory creation."""
    # Determine the base path for the project
    # Assuming the script is run from the project root or code directory
    current_dir = Path.cwd()
    
    # Look for the specific project directory
    project_code_root = current_dir / "projects" / "PROJ-951-llmxive-follow-up-extending-physisforcin" / "code"
    
    if not project_code_root.exists():
        # If not found in current structure, try relative to script location
        script_dir = Path(__file__).parent
        project_code_root = script_dir / "projects" / "PROJ-951-llmxive-follow-up-extending-physisforcin" / "code"
        
        if not project_code_root.exists():
            # Fallback: assume current dir is the code root if it contains 'projects'
            if (script_dir / "projects").exists():
                project_code_root = script_dir
            else:
                print(f"Could not locate project code root. Expected: {script_dir / 'projects' / 'PROJ-951-llmxive-follow-up-extending-physisforcin' / 'code'}")
                sys.exit(1)
    
    print(f"Creating T001b directories in: {project_code_root}")
    
    if create_t001b_directories(project_code_root):
        print("T001b task completed successfully.")
        sys.exit(0)
    else:
        print("T001b task failed due to directory creation errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()
