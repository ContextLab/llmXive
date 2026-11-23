import os
import sys
from pathlib import Path

def main():
    """
    Initialize the data directory structure for the llmXive project.
    Creates the following directories at the repository root:
    - data/
    - data/raw/
    - data/processed/
    - data/external/
    """
    # Determine the project root (parent of the 'code' directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    # Define data directory paths relative to project root
    data_root = project_root / "data"
    data_raw = data_root / "raw"
    data_processed = data_root / "processed"
    data_external = data_root / "external"

    # Create directories if they don't exist
    directories = [data_root, data_raw, data_processed, data_external]
    
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")

    # Create a .gitkeep file in data/raw to ensure it's tracked by git
    gitkeep_path = data_raw / ".gitkeep"
    if not gitkeep_path.exists():
        gitkeep_path.touch()
        print(f"Created .gitkeep in {data_raw}")

    print(f"Data directory structure initialized at: {data_root}")
    return 0

if __name__ == "__main__":
    sys.exit(main())