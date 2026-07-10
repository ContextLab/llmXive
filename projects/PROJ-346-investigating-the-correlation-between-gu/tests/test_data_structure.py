"""
Tests to verify the data directory structure creation.
"""
import os
import pytest
from pathlib import Path
import shutil
import tempfile

# Import the function to test
import sys
sys.path.insert(0, 'code')
from setup_data_structure import setup_data_structure

@pytest.fixture
def temp_data_root():
    """Create a temporary directory to simulate the project root."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_setup_data_structure_creates_directories(temp_data_root):
    """Test that the function creates the required directories."""
    result = setup_data_structure()
    
    expected_dirs = [
        "data/raw",
        "data/processed",
        "data/qc"
    ]
    
    for expected in expected_dirs:
        assert Path(expected).exists(), f"Directory {expected} was not created"
        assert Path(expected).is_dir(), f"{expected} is not a directory"
    
    assert len(result) == 3, "Function should return list of 3 created paths"

def test_setup_data_structure_handles_existing(temp_data_root):
    """Test that the function handles pre-existing directories gracefully."""
    # Create the directories manually first
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    
    # Run the function again
    result = setup_data_structure()
    
    # Should still succeed without error
    assert Path("data/raw").exists()
    assert Path("data/processed").exists()
    assert Path("data/qc").exists()