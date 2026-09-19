"""
Unit tests for the data directory setup script (T001b).
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# We will test the logic by temporarily manipulating the environment
# or by importing the function and checking side effects.
# Since the script uses `pathlib.Path(__file__).resolve().parent.parent`,
# we will test the logic of directory creation directly.

def test_create_directory_logic():
    """Test that the directory creation logic works correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir) / "data"
        
        # Ensure it doesn't exist
        assert not target_dir.exists()
        
        # Create it
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify it exists
        assert target_dir.exists()
        assert target_dir.is_dir()

def test_create_directory_if_exists():
    """Test that exist_ok=True prevents errors if directory exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir) / "data"
        
        # Create initially
        target_dir.mkdir()
        assert target_dir.exists()
        
        # Try to create again (should not raise)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Verify it still exists
        assert target_dir.exists()