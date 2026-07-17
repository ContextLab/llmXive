import os
import pytest
from pathlib import Path
import tempfile
import sys

# Add the code directory to the path so we can import the module
# This assumes the test is run from the project root or similar context
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from setup_data_dirs import setup_data_directories

def test_setup_data_directories_creates_all_folders():
    """Test that all required data directories are created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Run the setup function
        setup_data_directories(tmpdir)
        
        base_path = Path(tmpdir) / "data"
        
        # Verify each directory exists
        expected_dirs = ["raw", "interim", "processed", "external"]
        for dir_name in expected_dirs:
            dir_path = base_path / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"

def test_setup_data_directories_idempotent():
    """Test that running the setup function multiple times doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Run twice
        setup_data_directories(tmpdir)
        setup_data_directories(tmpdir)
        
        # Verify directories still exist
        base_path = Path(tmpdir) / "data"
        expected_dirs = ["raw", "interim", "processed", "external"]
        for dir_name in expected_dirs:
            assert (base_path / dir_name).exists()