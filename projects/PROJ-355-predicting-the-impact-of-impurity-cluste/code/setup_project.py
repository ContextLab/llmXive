import os
import sys
from pathlib import Path
from typing import List, Tuple

def ensure_directory(path: Path) -> bool:
    """
    Create a directory if it does not exist.
    Returns True if successful or if it already exists, False otherwise.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def create_gitkeep(path: Path) -> bool:
    """
    Create a .gitkeep file in the specified directory to ensure it is tracked by git.
    Returns True if successful, False otherwise.
    """
    gitkeep_file = path / ".gitkeep"
    try:
        if not gitkeep_file.exists():
            gitkeep_file.touch()
        return True
    except OSError as e:
        print(f"Error creating .gitkeep in {path}: {e}", file=sys.stderr)
        return False

def setup_directories(project_root: Path) -> List[Tuple[Path, bool]]:
    """
    Set up the standard project directory structure.
    Returns a list of (path, success) tuples.
    """
    directories = [
        project_root,
        project_root / "code",
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results",
        project_root / "tests",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
    ]

    results = []
    for dir_path in directories:
        success = ensure_directory(dir_path)
        if success:
            create_gitkeep(dir_path)
        results.append((dir_path, success))

    return results

def main() -> int:
    """
    Main entry point for setting up the project directory structure.
    Returns 0 on success, 1 on failure.
    """
    # Determine project root: projects/PROJ-355-predicting-the-impact-of-impurity-cluste/
    # Assuming this script is run from the repository root
    repo_root = Path.cwd()
    project_name = "PROJ-355-predicting-the-impact-of-impurity-cluste"
    project_root = repo_root / "projects" / project_name

    print(f"Setting up project structure at: {project_root}")

    results = setup_directories(project_root)

    all_success = True
    for path, success in results:
        status = "OK" if success else "FAILED"
        print(f"[{status}] {path}")
        if not success:
            all_success = False

    if all_success:
        print("Project structure setup complete.")
        return 0
    else:
        print("Project structure setup failed for some directories.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
