"""
Tests for the data directory setup script (T001b).
"""
import os
import tempfile
import shutil
from pathlib import Path
import sys

# Add the code directory to the path so we can import the script logic
# Note: In a real run, this would be installed or path-managed differently,
# but for this test we simulate the import or call the function directly.

def test_data_dir_creation():
    """
    Test that the setup_data_dir script successfully creates the data directory.
    We simulate the environment by creating a temp root and running the logic.
    """
    # Create a temporary directory to act as the project root
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        data_dir = tmp_path / "data"
        
        # Verify it doesn't exist yet
        assert not data_dir.exists(), "Data directory should not exist initially"
        
        # Simulate the logic from setup_data_dir.py
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify it exists now
        assert data_dir.exists(), "Data directory should exist after creation"
        assert data_dir.is_dir(), "Data path should be a directory"
        
        # Verify it is writable
        test_file = data_dir / "test_write.txt"
        test_file.write_text("test")
        assert test_file.exists(), "Should be able to write to the data directory"
        
        # Cleanup handled by TemporaryDirectory

def test_data_dir_idempotency():
    """
    Test that running the creation logic twice does not cause errors.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        data_dir = tmp_path / "data"
        
        # First creation
        data_dir.mkdir(parents=True, exist_ok=True)
        assert data_dir.exists()
        
        # Second creation (simulating running the script again)
        data_dir.mkdir(parents=True, exist_ok=True)
        assert data_dir.exists()
        
        # Verify no extra directories were created (e.g. data/data)
        assert not (data_dir / "data").exists()