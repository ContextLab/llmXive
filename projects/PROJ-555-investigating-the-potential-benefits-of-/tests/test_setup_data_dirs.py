"""
Tests for T008: Data directory structure creation.
"""
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# We will test the logic by mocking Path operations to avoid side effects on the actual file system
# or by running in a temporary directory if we want to test actual file creation.
# Given the constraints, let's test the logic of create_gitkeep and main with mocks.

from code.setup_data_dirs import create_gitkeep, main
from code.logging_config import setup_logging


def test_create_gitkeep_creates_file(tmp_path):
    """Test that create_gitkeep creates a .gitkeep file if it doesn't exist."""
    target_dir = tmp_path / "test_dir"
    target_dir.mkdir()
    gitkeep_path = target_dir / ".gitkeep"

    assert not gitkeep_path.exists()
    create_gitkeep(target_dir)
    assert gitkeep_path.exists()
    assert gitkeep_path.is_file()


def test_create_gitkeep_does_not_overwrite(tmp_path):
    """Test that create_gitkeep does not overwrite an existing .gitkeep file."""
    target_dir = tmp_path / "test_dir"
    target_dir.mkdir()
    gitkeep_path = target_dir / ".gitkeep"
    gitkeep_path.write_text("existing content")

    create_gitkeep(target_dir)
    assert gitkeep_path.read_text() == "existing content"


def test_main_creates_directories_and_gitkeeps(tmp_path, caplog):
    """Test that main creates the required directories and .gitkeep files."""
    # Mock Path.cwd to return our temp directory
    with patch('code.setup_data_dirs.Path.cwd', return_value=tmp_path):
        with patch('code.setup_data_dirs.ensure_directories'):
            with caplog.at_level("INFO"):
                main()

    # Check that directories were created
    expected_dirs = [
        tmp_path / "data" / "raw" / "landsat",
        tmp_path / "data" / "processed",
        tmp_path / "data" / "ecotourism",
    ]

    for dir_path in expected_dirs:
        assert dir_path.exists()
        assert dir_path.is_dir()
        assert (dir_path / ".gitkeep").exists()

    # Check for log messages
    assert "Starting T008" in caplog.text
    assert "completed successfully" in caplog.text