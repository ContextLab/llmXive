import os
import sys
from pathlib import Path

def main():
    """
    Create the directory structure for the project.
    Specifically creates 'code/' and 'tests/' directories
    relative to the project root.
    """
    # Determine project root based on the task context provided in tasks.md
    # The task specifies paths under 'projects/PROJ-712-predicting-individual-pain-sensitivity-f/'
    project_root = Path(__file__).resolve().parent.parent / "projects" / "PROJ-712-predicting-individual-pain-sensitivity-f"
    
    if not project_root.exists():
        # Fallback: if the script is run from a different context or the nested structure isn't fully set up yet,
        # create relative to the script's parent if that seems more appropriate, 
        # but strictly following the task description requires the specific project path.
        # Given T001a and T001b created data/artifacts, we assume the project root exists or is the target.
        # We will create the path relative to the script's parent if the specific project path doesn't exist yet,
        # to ensure the task completes successfully in a fresh environment.
        # However, the task explicitly names the path. Let's ensure we create the exact path requested.
        pass

    # Ensure the project root exists (create it if missing to allow subdirectory creation)
    project_root.mkdir(parents=True, exist_ok=True)

    # Define directories to create
    dirs_to_create = [
        project_root / "code",
        project_root / "tests"
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())