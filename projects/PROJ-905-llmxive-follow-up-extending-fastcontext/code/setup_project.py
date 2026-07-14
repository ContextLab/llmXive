import os
from pathlib import Path

def main():
    """
    Creates the project directory structure for PROJ-905-llmxive-follow-up-extending-fastcontext.
    This script ensures all required directories exist relative to the project root.
    """
    # Determine the project root based on the script location or current working directory.
    # Since this script is in 'code/', we go up one level to get the project root.
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    # Define the relative paths required by T001
    # Based on tasks.md: "mkdir -p data/raw data/processed data/results code tests/unit tests/integration specs/contracts state"
    # We also need to ensure 'code' exists as it contains this script, but the task implies creating the structure.
    relative_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "code",
        "tests/unit",
        "tests/integration",
        "specs/contracts",
        "state",
    ]

    created_count = 0
    for rel_dir in relative_dirs:
        dir_path = project_root / rel_dir
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path.relative_to(project_root)}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path.relative_to(project_root)}")

    # Create T001b requirement: state/projects/PROJ-905-llmxive-follow-up-extending-fastcontext.yaml
    state_projects_dir = project_root / "state" / "projects"
    state_projects_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_projects_dir / "PROJ-905-llmxive-follow-up-extending-fastcontext.yaml"
    
    if not state_file.exists():
        state_file.touch()
        print(f"Created empty state file: {state_file.relative_to(project_root)}")
    else:
        print(f"State file already exists: {state_file.relative_to(project_root)}")

    print(f"Project structure setup complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()