"""
Unit tests for the setup_directories module.
"""

import os
import tempfile
import pytest
from pathlib import Path
import shutil

# Import the function to test
# Assuming the module is in the 'code' directory relative to the test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from setup_directories import setup_directories


def test_setup_directories_creates_all_folders():
    """Test that setup_directories creates all required directories."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir)
        
        # Run the setup
        setup_directories(project_root)

        # Verify directories exist
        required_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "data/interim",
            "data/results",
            "tests/unit",
            "tests/integration",
            "docs",
            "state",
            "state/projects",
        ]

        for dir_name in required_dirs:
            full_path = project_root / dir_name
            assert full_path.exists(), f"Directory {full_path} was not created."
            assert full_path.is_dir(), f"{full_path} is not a directory."

def test_setup_directories_idempotent():
    """Test that running setup_directories twice does not cause errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_root = Path(tmp_dir)
        
        # Run twice
        setup_directories(project_root)
        setup_directories(project_root)

        # Verify directories still exist
        assert (project_root / "code").exists()
        assert (project_root / "data/raw").exists()