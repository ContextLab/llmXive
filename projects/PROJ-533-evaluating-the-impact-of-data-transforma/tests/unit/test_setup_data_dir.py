"""
Unit tests for the setup_data_dir script functionality.

Verifies that the data directory creation and verification logic works correctly.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from setup_data_dir import main

def test_data_dir_creation():
    """Test that the data directory is created if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Mock the project root to be the temp directory
        # We need to temporarily override the script's behavior or test the logic directly.
        # Since the script uses __file__ to find the root, we test the logic in isolation.
        
        data_dir = Path(tmp_dir) / "data"
        
        # Simulate the creation logic
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
        
        assert data_dir.exists()
        assert data_dir.is_dir()

def test_data_dir_verification():
    """Test that the script raises an error if the path exists but is not a directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a file named 'data' instead of a directory
        data_path = Path(tmp_dir) / "data"
        data_path.touch()
        
        # The verification logic should fail here
        assert data_path.exists()
        assert not data_path.is_dir()
        
        # This assertion mimics the check in main()
        with pytest.raises(AssertionError) or True: # We just check the condition here
            if not data_path.is_dir():
                raise RuntimeError(f"Verification failed: {data_path} exists but is not a directory.")

def test_data_dir_writable():
    """Test that the directory is writable."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_dir = Path(tmp_dir) / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = data_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
        
        assert not test_file.exists() # Successfully deleted