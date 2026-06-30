import os
from pathlib import Path
from config import get_config

def setup_data_directories():
    """
    Create the required data directory structure for the project.
    
    Creates the following directories under the project root:
    - data/stimuli/
    - data/responses/
    - data/processed/
    - data/stimuli_metadata/
    - data/ethics/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    config = get_config()
    project_root = config.get("project_root") or Path.cwd()
    
    data_dirs = [
        "data/stimuli",
        "data/responses",
        "data/processed",
        "data/stimuli_metadata",
        "data/ethics",
    ]
    
    success = True
    for dir_path in data_dirs:
        full_path = Path(project_root) / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            # Verify creation
            if not full_path.exists() or not full_path.is_dir():
                raise RuntimeError(f"Failed to create directory: {full_path}")
        except Exception as e:
            print(f"Error creating directory {full_path}: {e}")
            success = False
    
    return success

if __name__ == "__main__":
    import sys
    print("Setting up data directory structure...")
    if setup_data_directories():
        print("Data directories created successfully.")
        sys.exit(0)
    else:
        print("Failed to create some data directories.")
        sys.exit(1)
