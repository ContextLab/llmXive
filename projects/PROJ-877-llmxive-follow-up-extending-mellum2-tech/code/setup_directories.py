import os
from pathlib import Path

# Project root relative to this script's location context
# Assuming this script is run from the project root or code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_NAME = "PROJ-877-llmxive-follow-up-extending-mellum2-tech"

def ensure_data_directories():
    """
    Creates the required directory structure for the project's data artifacts.
    
    Creates:
    - projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/data/
    - projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/data/raw/
    - projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/data/processed/
    - projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/data/results/
    
    Returns:
        Path: The path to the created data root directory.
    """
    data_root = PROJECT_ROOT / PROJECT_NAME / "data"
    
    # Define subdirectories as per task T006 requirements
    subdirs = ["raw", "processed", "results"]
    
    for subdir in subdirs:
        dir_path = data_root / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory: {dir_path}")
    
    print(f"Data directory structure created at: {data_root}")
    return data_root

if __name__ == "__main__":
    ensure_data_directories()