import os
from pathlib import Path
from setup_directories import create_directories

def main() -> None:
    """
    Wrapper to ensure data and state directory structure is created.
    This script is specifically targeted for Task T004.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    # Specific directories for T004: data (raw, processed) and state
    data_dirs = [
        "data",
        "data/raw",
        "data/processed",
        "state"
    ]
    
    print(f"Ensuring data and state structure in {project_root}...")
    create_directories(project_root, data_dirs)
    print("Data and state directories ready.")
