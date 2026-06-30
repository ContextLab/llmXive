import os
from pathlib import Path

def setup_data_directories() -> None:
    """
    Creates the required data directory structure for the project.
    
    Creates the following directories relative to the project root:
    - data/raw
    - data/processed
    - data/interim
    - docs/outputs
    
    This function is idempotent; it will not fail if directories already exist.
    """
    # Determine project root (assumed to be the parent of the 'code' directory)
    # This script is located at code/setup_data_dirs.py
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    # Define relative paths as per task requirements
    directories = [
        "data/raw",
        "data/processed",
        "data/interim",
        "docs/outputs"
    ]
    
    created_count = 0
    for rel_path in directories:
        full_path = project_root / rel_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        else:
            # Verify it is a directory, not a file
            if not full_path.is_dir():
                raise NotADirectoryError(
                    f"Path exists but is not a directory: {full_path}"
                )
    
    # Log success (optional, but good practice for CLI tools)
    # In a real run, this could be routed to the logging system
    # For this implementation, we rely on the side effect of directory creation
    # as the primary output artifact.
    
if __name__ == "__main__":
    setup_data_directories()
