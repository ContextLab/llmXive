"""
Script to initialize the project's data directory structure.
Creates raw, processed, and artifacts directories with .gitkeep files.
"""
import os
import sys
from pathlib import Path

def setup_data_directories(project_root: Path) -> None:
    """Create the standard data directory structure."""
    data_base = project_root / "data"
    
    directories = [
        data_base / "raw",
        data_base / "processed",
        data_base / "artifacts",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        gitkeep_path = directory / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created: {gitkeep_path}")
        else:
            print(f"Exists: {gitkeep_path}")

def main():
    # Determine project root based on the task's specific path requirement
    # The task requires: projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff/
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    print(f"Project root detected at: {project_root}")
    setup_data_directories(project_root)
    print("Data directory setup complete.")

if __name__ == "__main__":
    main()