import os
import sys
from pathlib import Path

def setup_code_directories(project_root: Path) -> None:
    """
    Create the required subdirectories under the 'code/' directory.
    
    Structure:
    code/
      data/
      models/
      inference/
      evaluation/
      utils/
      tasks/
      tests/
    """
    base_dir = project_root / "code"
    base_dir.mkdir(parents=True, exist_ok=True)
    
    subdirs = [
        "data",
        "models",
        "inference",
        "evaluation",
        "utils",
        "tasks",
        "tests"
    ]
    
    for subdir in subdirs:
        dir_path = base_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

def main():
    # Determine project root (assuming script is at code/setup_directories.py)
    # We need to go up one level to get the project root relative to the script location
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    print(f"Project root detected at: {project_root}")
    setup_code_directories(project_root)
    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()
