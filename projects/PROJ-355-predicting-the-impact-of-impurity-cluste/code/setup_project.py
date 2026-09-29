import os
import sys
from pathlib import Path
from typing import List, Tuple

def get_project_root() -> Path:
    """Returns the root directory of the current project."""
    # Assuming the project root is the parent of the 'code' directory
    return Path(__file__).resolve().parent.parent

def ensure_directory(path: Path) -> bool:
    """Creates a directory if it does not exist. Returns True if successful."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}")
        return False

def create_gitkeep(path: Path) -> bool:
    """Creates a .gitkeep file in the specified directory to ensure it is tracked by git."""
    gitkeep_file = path / ".gitkeep"
    try:
        gitkeep_file.touch(exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating .gitkeep in {path}: {e}")
        return False

def setup_directories(base_path: Path, dir_names: List[str]) -> List[Tuple[str, bool]]:
    """
    Sets up a list of directories under base_path.
    Returns a list of tuples (directory_path_relative, success_status).
    """
    results = []
    for dir_name in dir_names:
        full_path = base_path / dir_name
        success = ensure_directory(full_path)
        if success:
            create_gitkeep(full_path)
        results.append((str(full_path.relative_to(base_path)), success))
    return results

def main():
    """
    Main function to initialize the project directory structure.
    Creates the root project directory and all required subdirectories.
    """
    # Define the project root name
    project_root_name = "projects/PROJ-355-predicting-the-impact-of-impurity-cluste"
    
    # Define the subdirectories to create
    # Using forward slashes for path construction which pathlib handles correctly
    subdirs = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "tests/unit",
        "tests/integration"
    ]

    # Determine the absolute path for the project root
    # We assume the script is run from the repository root or code directory
    # We need to create the project root relative to the current working directory
    # or the script's location? The task says "Create root directory projects/..."
    # Let's assume we run from the repo root.
    current_working_dir = Path.cwd()
    project_root_path = current_working_dir / project_root_name

    print(f"Initializing project structure at: {project_root_path}")

    # Create the root project directory
    if not ensure_directory(project_root_path):
        print("Failed to create project root directory. Exiting.")
        sys.exit(1)

    # Create subdirectories
    print("Creating subdirectories...")
    results = setup_directories(project_root_path, subdirs)

    success_count = 0
    for rel_path, success in results:
        status = "Created" if success else "Failed"
        print(f"{status}: {rel_path}")
        if success:
            success_count += 1

    if success_count == len(subdirs):
        print(f"Successfully initialized project structure with {success_count} subdirectories.")
        return 0
    else:
        print(f"Completed with {len(subdirs) - success_count} errors.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
