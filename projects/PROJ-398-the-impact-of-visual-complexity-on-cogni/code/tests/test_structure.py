import os
import sys
from pathlib import Path
import pytest
from setup_data_directories import main as run_structure_creation

def test_data_directories_exist():
    """
    Verify that the required data directory structure exists:
    data/stimuli/, data/processed/, data/measurements/, data/raw/
    """
    # Ensure the directories are created before asserting
    run_structure_creation()
    
    base_dir = Path("data")
    
    required_dirs = [
        base_dir / "stimuli",
        base_dir / "processed",
        base_dir / "measurements",
        base_dir / "raw"
    ]
    
    for dir_path in required_dirs:
        assert dir_path.exists(), f"Directory {dir_path} does not exist."
        assert dir_path.is_dir(), f"Path {dir_path} is not a directory."
