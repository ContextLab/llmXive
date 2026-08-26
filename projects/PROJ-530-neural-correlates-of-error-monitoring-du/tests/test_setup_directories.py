import os
import shutil
import pytest
from pathlib import Path
import sys

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import create_project_directories

PROJECT_ROOT = "projects/PROJ-530-neural-correlates-of-error-monitoring-du"
DATA_RAW = os.path.join(PROJECT_ROOT, "data", "raw")
DATA_PROCESSED = os.path.join(PROJECT_ROOT, "data", "processed")

@pytest.fixture(autouse=True)
def cleanup_directories():
    """Clean up directories before and after each test."""
    # Remove if exists
    if os.path.exists(PROJECT_ROOT):
        shutil.rmtree(PROJECT_ROOT)
    yield
    # Clean up after test
    if os.path.exists(PROJECT_ROOT):
        shutil.rmtree(PROJECT_ROOT)

def test_create_data_directories():
    """Test that create_project_directories creates the required data directories."""
    result = create_project_directories()
    
    assert result is True, "Directory creation should return True on success"
    assert os.path.isdir(DATA_RAW), f"Directory {DATA_RAW} should exist"
    assert os.path.isdir(DATA_PROCESSED), f"Directory {DATA_PROCESSED} should exist"

def test_directories_are_empty():
    """Test that the created directories are initially empty."""
    create_project_directories()
    
    raw_files = os.listdir(DATA_RAW)
    processed_files = os.listdir(DATA_PROCESSED)
    
    assert len(raw_files) == 0, f"Directory {DATA_RAW} should be empty"
    assert len(processed_files) == 0, f"Directory {DATA_PROCESSED} should be empty"

def test_nested_structure_created():
    """Test that parent directories are created if they don't exist."""
    # Remove the entire project root to ensure nested creation
    if os.path.exists(PROJECT_ROOT):
        shutil.rmtree(PROJECT_ROOT)
        
    assert not os.path.exists(PROJECT_ROOT)
    
    result = create_project_directories()
    
    assert result is True
    assert os.path.isdir(PROJECT_ROOT)
    assert os.path.isdir(DATA_RAW)
    assert os.path.isdir(DATA_PROCESSED)