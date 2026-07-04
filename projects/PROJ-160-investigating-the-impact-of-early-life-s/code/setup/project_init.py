import os
import sys
from pathlib import Path

# Define the project root path relative to the repository root
PROJECT_SLUG = "PROJ-160-investigating-the-impact-of-early-life-s"
REQUIRED_SUBDIRS = [
    "code",
    "data/raw",
    "data/processed",
    "tests",
    "contracts"
]

def get_project_path(base_path: Path) -> Path:
    """
    Constructs the full path to the project directory.
    """
    return base_path / PROJECT_SLUG

def verify_and_create_structure(base_path: Path) -> dict:
    """
    Verifies the existence of the project directory and required subdirectories.
    Creates them if they are missing.
    
    Args:
        base_path: The root directory of the repository (e.g., where this script is run).
        
    Returns:
        A dictionary with 'success' (bool) and 'created' (list of created paths).
    """
    project_root = get_project_path(base_path)
    created_paths = []
    
    # Ensure project root exists
    if not project_root.exists():
        project_root.mkdir(parents=True, exist_ok=True)
        created_paths.append(str(project_root))
    
    # Ensure subdirectories exist
    for subdir in REQUIRED_SUBDIRS:
        dir_path = project_root / subdir
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(dir_path))
            
    return {
        "success": True,
        "project_root": str(project_root),
        "created_paths": created_paths
    }

def main():
    """
    Entry point for the project initialization script.
    """
    # Determine the base path (current working directory or repository root)
    # Assuming this script is run from the repository root
    base_path = Path.cwd()
    
    print(f"Initializing project structure at: {base_path / PROJECT_SLUG}")
    
    try:
        result = verify_and_create_structure(base_path)
        
        if result["success"]:
            print("Project structure verification/completion successful.")
            if result["created_paths"]:
                print(f"Created the following directories:")
                for path in result["created_paths"]:
                    print(f"  - {path}")
            else:
                print("All required directories already existed.")
            return 0
        else:
            print("Failed to verify or create project structure.")
            return 1
    except Exception as e:
        print(f"Error during project initialization: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())