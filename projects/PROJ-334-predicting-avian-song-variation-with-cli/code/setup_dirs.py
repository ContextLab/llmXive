"""
Directory structure setup for the Avian Song Variation project.
Creates the required directory hierarchy as per T001a.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the base project root
    # The task specifies creating directories at the project root relative to the repo
    # We assume the script runs from the project root or we calculate it relative to this file
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    # Define the directories to create based on T001a
    # The task asks for: projects/PROJ-334-predicting-avian-song-variation-with-cli/, data/, code/, tests/
    # However, looking at the existing API surface, files like code/config.py exist at the root 'code/'
    # and the task description for T001a says "Create directory structure at projects/..., data/, code/, tests/"
    # This implies the project root IS the repo root, and we need to ensure these top-level dirs exist.
    # The 'projects/PROJ-334...' part of the task description might be a template artifact or referring to a specific
    # sub-project location. Given the existing file structure (code/config.py exists), the 'code' directory
    # is already at the root. We will ensure the standard dirs (data, code, tests) exist at the root.
    # We will also create the specific project folder if it doesn't exist to satisfy the literal task text.
    
    dirs_to_create = [
        project_root / "data",
        project_root / "code",
        project_root / "tests",
        # The task explicitly mentions this path, so we ensure it exists too
        project_root / "projects" / "PROJ-334-predicting-avian-song-variation-with-cli"
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path.relative_to(project_root)}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path.relative_to(project_root)}")

    print(f"Setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())