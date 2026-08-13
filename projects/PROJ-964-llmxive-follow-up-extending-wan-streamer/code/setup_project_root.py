import os
import sys
from pathlib import Path

def setup_project_root():
    """
    Create the project root directory: projects/PROJ-964-llmxive-follow-up-extending-wan-streamer/
    Returns the path to the created directory.
    """
    base_path = Path(__file__).resolve().parent.parent
    projects_dir = base_path / "projects"
    project_name = "PROJ-964-llmxive-follow-up-extending-wan-streamer"
    
    target_path = projects_dir / project_name
    
    os.makedirs(target_path, exist_ok=True)
    print(f"Created project directory: {target_path}")
    
    return target_path

def verify_project_root():
    """
    Verify that the project root directory exists.
    Returns True if it exists, False otherwise.
    """
    base_path = Path(__file__).resolve().parent.parent
    projects_dir = base_path / "projects"
    project_name = "PROJ-964-llmxive-follow-up-extending-wan-streamer"
    
    target_path = projects_dir / project_name
    
    if not os.path.exists(target_path):
        print(f"ERROR: Project directory does not exist: {target_path}")
        return False
    else:
        print(f"Verified: {target_path}")
        return True

def main():
    """
    Main entry point to create and verify project root directory.
    """
    print("Setting up project root directory...")
    path = setup_project_root()
    
    print("\nVerifying project root directory...")
    if verify_project_root():
        print("\nProject root directory exists.")
        return 0
    else:
        print("\nProject root directory is missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())