import os
import sys
from pathlib import Path

# Define the required directory structure relative to the project root
REQUIRED_DIRS = [
    "data/raw",
    "data/derived",
    "data/gold_standard",
    "artifacts",
]

def setup_directories(base_path: Path = None) -> None:
    """
    Creates the required data directory structure if they do not exist.
    
    Args:
        base_path: The root directory of the project. Defaults to the current working directory.
    
    Raises:
        OSError: If a directory cannot be created due to permissions or other OS-level issues.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    # Ensure base_path is a Path object
    if isinstance(base_path, str):
        base_path = Path(base_path)

    created_count = 0
    for dir_name in REQUIRED_DIRS:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Setup complete. {created_count} new directories created.")

def main():
    """
    CLI entry point for setting up data directories.
    """
    # Default to the directory containing the script if called directly, 
    # otherwise use current working directory.
    # In the context of the project, we usually run from the root, 
    # but scripts might be invoked from subdirectories.
    # We assume the project root is the parent of 'scripts' if we are in 'code/scripts'.
    current_file = Path(__file__).resolve()
    # Heuristic: If running from code/scripts, go up one level to 'code' or project root?
    # The task says paths are relative to project root. 
    # Let's assume the script is run from the project root or we pass the root as an arg.
    # For simplicity and robustness, we default to the current working directory (CWD)
    # which is the standard behavior for CLI tools unless specified otherwise.
    
    setup_directories()

if __name__ == "__main__":
    main()
