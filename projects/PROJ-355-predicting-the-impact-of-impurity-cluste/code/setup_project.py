import os
import sys
from pathlib import Path
from typing import List, Tuple

# Constants
PROJECT_NAME = "PROJ-355-predicting-the-impact-of-impurity-cluste"
PROJECT_ROOT_NAME = "projects"

# Directory structure to create
REQUIRED_DIRS: List[str] = [
    "code",
    "data/raw",
    "data/processed",
    "results",
    "tests/unit",
    "tests/integration",
]

def get_project_root() -> Path:
    """Returns the absolute path to the project root directory."""
    base = Path(__file__).resolve().parent.parent
    return base / PROJECT_ROOT_NAME / PROJECT_NAME

def ensure_directory(path: Path) -> bool:
    """
    Creates the directory if it does not exist.
    Returns True if created or already exists, False on failure.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}")
        return False

def create_gitkeep(path: Path) -> None:
    """Creates a .gitkeep file in the given directory to ensure it is tracked by git."""
    gitkeep_path = path / ".gitkeep"
    if not gitkeep_path.exists():
        gitkeep_path.touch()

def setup_directories() -> Tuple[bool, List[str]]:
    """
    Initializes the project directory structure idempotently.
    Returns (success, list_of_created_paths).
    """
    project_root = get_project_root()
    created_paths = []
    
    # Ensure root exists
    if not ensure_directory(project_root):
        return False, []
    
    created_paths.append(str(project_root))

    # Create subdirectories
    for dir_name in REQUIRED_DIRS:
        target_path = project_root / dir_name
        if ensure_directory(target_path):
            created_paths.append(str(target_path))
            create_gitkeep(target_path)
            print(f"Created/Verified: {target_path}")
        else:
            print(f"Failed to create: {target_path}")
            return False, created_paths

    print(f"Project structure initialized at: {project_root}")
    return True, created_paths

def main() -> int:
    """Entry point for script execution."""
    print(f"Initializing project: {PROJECT_NAME}")
    success, paths = setup_directories()
    if success:
        print("Success. Directories created/verified:")
        for p in paths:
            print(f"  - {p}")
        return 0
    else:
        print("Failed to initialize some directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
