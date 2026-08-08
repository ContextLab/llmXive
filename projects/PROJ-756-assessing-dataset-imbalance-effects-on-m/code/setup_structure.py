import os
import sys
from pathlib import Path

def create_directories(project_root: Path) -> None:
    """
    Creates the full directory structure for the project.
    
    Structure:
    projects/<project_id>/
        data/
            raw/
        code/
        tests/
        artifacts/
        results/
        state/
        logs/
            archive/
    """
    base_path = project_root / "projects" / "PROJ-756-assessing-dataset-imbalance-effects-on-m"
    
    directories = [
        base_path / "data" / "raw",
        base_path / "code",
        base_path / "tests",
        base_path / "artifacts",
        base_path / "results",
        base_path / "state",
        base_path / "logs" / "archive",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def main() -> None:
    """Entry point to create the project directory structure."""
    # Define the project root relative to the current working directory
    # Assuming the script is run from the repository root
    project_root = Path.cwd()
    
    print(f"Creating project structure at: {project_root}")
    create_directories(project_root)
    print("Project structure creation complete.")

if __name__ == "__main__":
    main()
