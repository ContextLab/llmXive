import os
from pathlib import Path
from typing import List

def ensure_directory(path: Path) -> None:
    """Ensure the given directory path exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True)

def create_init_file(path: Path) -> None:
    """Create an empty __init__.py file in the given directory."""
    init_file = path / "__init__.py"
    init_file.touch(exist_ok=True)

def main() -> None:
    """Create the required code directory structure."""
    # Define the required directories relative to the project root
    # Assuming the script runs from the project root or code/ directory
    # We will create them relative to the current working directory if not specified otherwise,
    # but typically these are project-root relative.
    # Based on task description: `src/lib/`, `src/metrics/`, `src/experiment/`, `src/analysis/`, `tests/`
    
    # We assume the project root is the parent of the `code` directory or the script is run from root.
    # To be safe and consistent with the task description which lists paths like `src/lib/`,
    # we will create them relative to the current working directory (assumed to be project root).
    
    # However, looking at the existing files, they are in `code/`.
    # The task says: "Create code directory structure (`src/lib/`, ...)"
    # If this script is in `code/`, we should probably create `src/` and `tests/` in the parent.
    # Let's assume the script is executed from the project root, or we create relative to where it is.
    # Given the existing structure in `code/`, let's create the directories relative to the script's location's parent
    # to match the `src/` and `tests/` at repository root convention mentioned in `tasks.md`.
    
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent # Assuming code/ is at repo root or similar structure

    directories = [
        project_root / "src" / "lib",
        project_root / "src" / "metrics",
        project_root / "src" / "experiment",
        project_root / "src" / "analysis",
        project_root / "tests",
    ]

    for dir_path in directories:
        ensure_directory(dir_path)
        create_init_file(dir_path)

    # Also ensure the parent `src` directory exists if it didn't have any subdirs created yet
    # (though the loop above handles subdirs, the parent `src` might not have an __init__.py if not needed,
    # but usually it's good practice. The task specifically lists subdirs).
    # The task asks for `src/lib/`, `src/metrics/`, etc.
    
    # Create __init__.py for `src` as well to make it a package
    src_dir = project_root / "src"
    ensure_directory(src_dir)
    create_init_file(src_dir)

    print(f"Created directory structure at {project_root}")
    for d in directories:
        print(f"  - {d}")

if __name__ == "__main__":
    main()
