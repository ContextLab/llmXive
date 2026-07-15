"""
Unit tests for the data directory structure setup.

Tests verify that:
1. The data directory structure is created correctly.
2. The directories exist after running the setup script.
3. The directories are actual directories (not files).
"""
import os
import tempfile
import pytest
from pathlib import Path

# Import the function to test
# We need to adjust the import path based on where this test runs from
# Assuming the test runs from the project root or code is in PYTHONPATH
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.setup_data_dirs import setup_data_directories

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate a project root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_setup_creates_directories(temp_project_root, monkeypatch):
    """Test that setup_data_directories creates the required directories."""
    # Mock the __file__ attribute of the module to use our temp directory
    # We need to patch the module that contains the function
    import code.setup_data_dirs as setup_module
    
    original_path = setup_module.__file__
    # Create a fake path structure: temp_project_root/code/setup_data_dirs.py
    fake_code_dir = temp_project_root / "code"
    fake_code_dir.mkdir()
    fake_script_path = fake_code_dir / "setup_data_dirs.py"
    fake_script_path.touch()
    
    # Temporarily replace __file__ in the module
    setup_module.__file__ = str(fake_script_path)
    
    try:
        # Run the setup function
        setup_data_directories()
        
        # Check that the directories were created
        data_root = temp_project_root / "data"
        assert data_root.exists(), "Root data directory should exist"
        assert data_root.is_dir(), "Root data path should be a directory"
        
        raw_dir = data_root / "raw"
        assert raw_dir.exists(), "Raw directory should exist"
        assert raw_dir.is_dir(), "Raw path should be a directory"
        
        interim_dir = data_root / "interim"
        assert interim_dir.exists(), "Interim directory should exist"
        assert interim_dir.is_dir(), "Interim path should be a directory"
        
        processed_dir = data_root / "processed"
        assert processed_dir.exists(), "Processed directory should exist"
        assert processed_dir.is_dir(), "Processed path should be a directory"
    finally:
        # Restore original __file__
        setup_module.__file__ = original_path

def test_setup_idempotent(temp_project_root, monkeypatch):
    """Test that running setup multiple times doesn't cause errors."""
    import code.setup_data_dirs as setup_module
    
    original_path = setup_module.__file__
    fake_code_dir = temp_project_root / "code"
    fake_code_dir.mkdir()
    fake_script_path = fake_code_dir / "setup_data_dirs.py"
    fake_script_path.touch()
    
    setup_module.__file__ = str(fake_script_path)
    
    try:
        # Run setup twice
        setup_data_directories()
        setup_data_directories()
        
        # Verify directories still exist
        data_root = temp_project_root / "data"
        assert (data_root / "raw").exists()
        assert (data_root / "interim").exists()
        assert (data_root / "processed").exists()
    finally:
        setup_module.__file__ = original_path