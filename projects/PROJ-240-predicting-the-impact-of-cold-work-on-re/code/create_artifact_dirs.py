import os
from pathlib import Path

def main():
    """
    Create all necessary directories and .gitkeep files for the project.
    """
    # Determine project root
    # Assuming this script is in code/ directory
    project_root = Path(__file__).resolve().parent.parent
    project_name = project_root.name
    full_project_path = project_root / project_name

    # Define directories to create
    dirs_to_create = [
        full_project_path / "code",
        full_project_path / "tests",
        full_project_path / "data" / "raw",
        full_project_path / "data" / "processed",
        full_project_path / "data" / "split",
        full_project_path / "artifacts" / "models",
        full_project_path / "artifacts" / "reports",
        full_project_path / "artifacts" / "figures",
    ]

    # Create directories and .gitkeep files
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.write_text("")
        print(f"Created: {dir_path}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()
