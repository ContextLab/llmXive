"""
Tests for the directory setup functionality.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch

# Import the function to test
from setup_directories import setup_data_directories, main
from config import get_project_root


def test_setup_data_directories_creates_structure(tmp_path):
    """
    Test that setup_data_directories creates the required directories.
    Uses a temporary path to avoid modifying the actual project structure.
    """
    # Mock get_project_root to return our temporary path
    with patch('setup_directories.get_project_root', return_value=tmp_path):
        result = setup_data_directories()

    # Verify the structure was created
    assert result["data"].exists()
    assert result["raw"].exists()
    assert result["processed"].exists()
    assert result["data"] == tmp_path / "data"
    assert result["raw"] == tmp_path / "data" / "raw"
    assert result["processed"] == tmp_path / "data" / "processed"


def test_setup_data_directories_idempotent(tmp_path):
    """
    Test that running setup_data_directories multiple times doesn't cause errors.
    """
    with patch('setup_directories.get_project_root', return_value=tmp_path):
        # Run twice
        result1 = setup_data_directories()
        result2 = setup_data_directories()

    # Both runs should succeed and return the same paths
    assert result1["raw"].exists()
    assert result2["raw"].exists()
    assert result1["raw"] == result2["raw"]


def test_main_success(tmp_path, capsys):
    """
    Test the main() function execution path.
    """
    with patch('setup_directories.get_project_root', return_value=tmp_path):
        exit_code = main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Successfully created directory structure" in captured.out