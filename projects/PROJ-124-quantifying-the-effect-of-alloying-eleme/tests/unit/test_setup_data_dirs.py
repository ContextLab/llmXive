import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
# We assume the code is in code/utils/setup_data_dirs.py
# The import path must match the project structure
sys_path_backup = list(__import__('sys').path)
try:
    # Add the project root to path if not already there
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in __import__('sys').path:
        __import__('sys').path.insert(0, str(project_root))
    
    from utils.setup_data_dirs import create_data_directories
finally:
    __import__('sys').path[:] = sys_path_backup

def test_creates_raw_and_processed_directories():
    """
    Test that create_data_directories creates data/raw and data/processed.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        
        # Ensure data folder doesn't exist yet
        data_folder = base_path / "data"
        assert not data_folder.exists()
        
        # Run the function
        create_data_directories(base_path)
        
        # Verify directories exist
        raw_dir = base_path / "data" / "raw"
        processed_dir = base_path / "data" / "processed"
        
        assert raw_dir.exists(), f"Directory {raw_dir} was not created"
        assert processed_dir.exists(), f"Directory {processed_dir} was not created"
        assert raw_dir.is_dir(), f"{raw_dir} is not a directory"
        assert processed_dir.is_dir(), f"{processed_dir} is not a directory"

def test_handles_existing_directories():
    """
    Test that the function does not fail if directories already exist.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_path = Path(tmp_dir)
        
        # Pre-create the directories
        (base_path / "data" / "raw").mkdir(parents=True)
        (base_path / "data" / "processed").mkdir(parents=True)
        
        # Run the function - should not raise
        create_data_directories(base_path)
        
        # Verify they still exist
        assert (base_path / "data" / "raw").exists()
        assert (base_path / "data" / "processed").exists()