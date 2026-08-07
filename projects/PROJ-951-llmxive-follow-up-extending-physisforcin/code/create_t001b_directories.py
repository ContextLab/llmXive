import os
import sys
from pathlib import Path

def create_t001b_directories(project_root: Path) -> None:
    """
    Creates the primary subdirectories for the project:
    - src/
    - tests/
    - data/

    These directories are the foundational structure required for the rest of the project.
    """
    dirs_to_create = [
        "src",
        "tests",
        "data"
    ]

    created_count = 0
    for dir_name in dirs_to_create:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"T001b Directory Creation Summary: {created_count} new directories created.")
    return created_count

if __name__ == "__main__":
    # Default to current directory if no argument provided, or use provided path
    if len(sys.argv) > 1:
        root = Path(sys.argv[1])
    else:
        root = Path.cwd()

    # Ensure we are operating within the expected project context
    # The task specifies: projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/
    # We assume this script is run from 'code' or passed the 'code' path.
    create_t001b_directories(root)
