"""
Unit tests for the directory setup functionality (T008).
"""
import os
import tempfile
from pathlib import Path
import pytest

# Mock the config module to avoid dependency on full project root setup during tests
import sys
from unittest.mock import patch, MagicMock

# Prepare the module for import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.setup_directories import create_directories


def test_create_directories_creates_missing():
    """Test that create_directories actually creates the required folders."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock get_project_root to return our temp directory
        with patch('data.setup_directories.get_project_root', return_value=Path(tmpdir)):
            result = create_directories()
            
            # Check that the list is not empty
            assert len(result) > 0
            
            # Verify specific directories exist
            data_root = Path(tmpdir) / "data"
            assert data_root.exists()
            assert (data_root / "raw").exists()
            assert (data_root / "processed").exists()
            
            # Verify the returned paths match what we expect
            assert Path(tmpdir) / "data" / "raw" in result
            assert Path(tmpdir) / "data" / "processed" in result


def test_create_directories_idempotent():
    """Test that running create_directories twice doesn't cause errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('data.setup_directories.get_project_root', return_value=Path(tmpdir)):
            # First run
            result1 = create_directories()
            assert len(result1) > 0
            
            # Second run
            result2 = create_directories()
            assert len(result2) > 0
            
            # Verify they are the same paths
            assert result1 == result2