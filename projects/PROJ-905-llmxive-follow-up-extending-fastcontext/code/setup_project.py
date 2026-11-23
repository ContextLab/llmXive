import os
from pathlib import Path

def main():
    """
    Create the project directory structure for PROJ-905-llmxive-follow-up-extending-fastcontext.
    Ensures all required directories exist relative to the project root.
    """
    # Define the base project root
    # The script is located in code/, so we go up one level to find the project root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Define relative paths required by T001
    # Note: The task description mentions `projects/PROJ-.../` but the context implies
    # the current working directory IS that project root. We create the subdirs relative here.
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "code",
        "tests/unit",
        "tests/integration",
        "specs/contracts",
        "state"
    ]

    created_count = 0
    for rel_dir in required_dirs:
        target_path = project_root / rel_dir
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {target_path}")
        else:
            # Ensure it is a directory, not a file
            if not target_path.is_dir():
                raise FileExistsError(f"Path exists but is not a directory: {target_path}")

    print(f"Project structure verification complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    exit(main())
