import os
import sys
from pathlib import Path

def create_directories(project_root: str) -> None:
    """
    Create the required code directory structure for the project.
    
    Specifically creates:
    - code/data/
    - code/tests/
    - code/utils/
    
    Args:
        project_root: The absolute or relative path to the project root directory.
    """
    base_path = Path(project_root)
    
    # Define the directories to create relative to the project root
    directories = [
        base_path / "code" / "data",
        base_path / "code" / "tests",
        base_path / "code" / "utils"
    ]
    
    for directory in directories:
        # Create the directory and any parent directories if they don't exist
        # exist_ok=True prevents errors if the directory already exists
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def main() -> None:
    """
    Main entry point for the directory creation script.
    
    Expects the project root to be provided as a command-line argument.
    If no argument is provided, defaults to the current working directory
    (assuming the script is run from the project root).
    """
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    print(f"Creating code directories in: {os.path.abspath(project_root)}")
    create_directories(project_root)
    print("Directory creation complete.")

if __name__ == "__main__":
    main()