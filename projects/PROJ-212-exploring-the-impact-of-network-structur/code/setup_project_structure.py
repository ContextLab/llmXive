import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure as specified in T001.
    Directories created relative to the project root:
    - src/
    - tests/
    - data/
        - raw/
        - processed/
    - results/
    - state/
    """
    # Define the base directory (current working directory or project root)
    # In the context of the pipeline, this script is run from the project root.
    base_path = Path.cwd()

    # Define relative paths as per task description
    # Note: The task description mentions 'src/', but the existing API surface
    # shows files in 'code/' (e.g., code/src/...).
    # However, T001 explicitly says: "Create project structure... by executing: mkdir -p src tests data results data/raw data/processed state".
    # And the note says: "Plan defines `src/` at repository root, not `projects/.../code/`."
    # We will follow the explicit mkdir command in the task description.
    # If the existing code is in 'code/', we create 'src/' as requested by T001.
    # The existing files in 'code/' might be a legacy or alternative structure,
    # but T001 is the source of truth for this specific task.
    
    directories = [
        "src",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "results",
        "state"
    ]

    created_count = 0
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            # Verify it's actually a directory
            if dir_path.is_dir():
                print(f"Directory already exists: {dir_path}")
            else:
                print(f"Warning: Path exists but is not a directory: {dir_path}")

    if created_count == 0:
        print("No new directories were created. Structure already exists.")
    else:
        print(f"Successfully created {created_count} directory/directories.")

    return 0

if __name__ == "__main__":
    sys.exit(main())