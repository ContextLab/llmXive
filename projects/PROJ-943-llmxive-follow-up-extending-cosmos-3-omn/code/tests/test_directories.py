"""
Integration tests to verify directory structure creation.
These tests ensure that the project's required directory structure is correctly set up.
"""
import os
import sys
import pytest
from pathlib import Path

# Add parent directory to path to import scripts
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.create_directories import create_directory, main


@pytest.fixture
def temp_base_path(tmp_path):
    """Provide a temporary base path for testing directory creation."""
    return tmp_path


def test_scripts_directory_exists(temp_base_path):
    """Test that the scripts directory can be created."""
    target = temp_base_path / "scripts"
    result = create_directory(target)
    assert result is True
    assert target.exists()
    assert target.is_dir()


def test_raw_data_directory_exists(temp_base_path):
    """Test that the raw data directory can be created."""
    target = temp_base_path / "data" / "raw"
    result = create_directory(target)
    assert result is True
    assert target.exists()
    assert target.is_dir()


def test_processed_data_directory_exists(temp_base_path):
    """Test that the processed data directory can be created."""
    target = temp_base_path / "data" / "processed"
    result = create_directory(target)
    assert result is True
    assert target.exists()
    assert target.is_dir()


def test_splits_directory_exists(temp_base_path):
    """Test that the splits directory can be created."""
    target = temp_base_path / "data" / "splits"
    result = create_directory(target)
    assert result is True
    assert target.exists()
    assert target.is_dir()


def test_models_directory_exists(temp_base_path):
    """Test that the models directory can be created."""
    target = temp_base_path / "models"
    result = create_directory(target)
    assert result is True
    assert target.exists()
    assert target.is_dir()


def test_tests_directory_exists(temp_base_path):
    """Test that the tests directory can be created."""
    target = temp_base_path / "tests"
    result = create_directory(target)
    assert result is True
    assert target.exists()
    assert target.is_dir()


def test_all_directories_exist(temp_base_path):
    """Test the full suite of directory creation."""
    dirs = [
        "scripts",
        "data/raw",
        "data/processed",
        "data/splits",
        "models",
        "tests"
    ]
    for d in dirs:
        target = temp_base_path / d
        assert create_directory(target)
        assert target.exists()
        assert target.is_dir()