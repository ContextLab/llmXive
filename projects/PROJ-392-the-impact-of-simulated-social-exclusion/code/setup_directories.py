import os
from pathlib import Path

def create_directories(base_path: Path) -> None:
    """
    Create the required directory structure for the project.
    
    Creates the following directories relative to base_path:
    - data/raw-fmri
    - data/processed-fmri
    - data/behavioral
    - data/results
    - code/manipulation
    - code/utils
    
    Args:
        base_path: The root directory of the project.
    """
    # Define the directories to create
    directories = [
        "data/raw-fmri",
        "data/processed-fmri",
        "data/behavioral",
        "data/results",
        "code/manipulation",
        "code/utils",
    ]
    
    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def main() -> None:
    """Main entry point for the directory setup script."""
    # Determine the project root (parent of 'code' directory where this script lives)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    print(f"Project root: {project_root}")
    create_directories(project_root)
    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()