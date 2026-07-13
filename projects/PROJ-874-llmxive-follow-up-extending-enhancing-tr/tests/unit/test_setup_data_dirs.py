"""
Unit tests for the data directory setup script.
"""
import os
import tempfile
import shutil
import pytest
import sys

# Add the parent directory (project root) to the path to import the code module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.setup_data_dirs import setup_data_directories

def test_setup_creates_directories():
    """Test that setup_data_directories creates the expected folder structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Call the function
        setup_data_directories(tmpdir)

        # Verify directories exist
        expected_dirs = [
            os.path.join(tmpdir, "data", "raw"),
            os.path.join(tmpdir, "data", "processed"),
            os.path.join(tmpdir, "data", "results")
        ]

        for d in expected_dirs:
            assert os.path.exists(d), f"Directory {d} was not created"
            assert os.path.isdir(d), f"{d} exists but is not a directory"

def test_setup_idempotent():
    """Test that running setup again does not raise errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Run once
        setup_data_directories(tmpdir)
        
        # Run again
        # Should not raise an exception
        setup_data_directories(tmpdir)

        # Verify structure is still intact
        assert os.path.exists(os.path.join(tmpdir, "data", "raw"))
        assert os.path.exists(os.path.join(tmpdir, "data", "processed"))
        assert os.path.exists(os.path.join(tmpdir, "data", "results"))