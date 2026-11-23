"""Unit tests for the setup_data_dirs script (Task T005).

These tests verify that:
1. The required directories (data/raw, data/processed, data/consent) are created.
2. Each directory contains a .gitkeep file.
3. The directories are empty except for the .gitkeep file.
"""

import os
import shutil
import tempfile
from pathlib import Path
import pytest

# We need to mock the config to use a temporary directory
import sys
from unittest.mock import patch

from setup_data_dirs import create_directories


@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mocked_config(temp_project_root):
    """Mock the config functions to use our temporary directory."""
    with patch("setup_data_dirs.get_project_root", return_value=temp_project_root), \
         patch("setup_data_dirs.get_raw_data_dir", return_value=temp_project_root / "data" / "raw"), \
         patch("setup_data_dirs.get_processed_data_dir", return_value=temp_project_root / "data" / "processed"), \
         patch("setup_data_dirs.get_consent_dir", return_value=temp_project_root / "data" / "consent"):
        yield


def test_directories_created(mocked_config, temp_project_root):
    """Test that the required directories are created."""
    create_directories()

    raw_dir = temp_project_root / "data" / "raw"
    processed_dir = temp_project_root / "data" / "processed"
    consent_dir = temp_project_root / "data" / "consent"

    assert raw_dir.exists(), "data/raw directory should exist"
    assert processed_dir.exists(), "data/processed directory should exist"
    assert consent_dir.exists(), "data/consent directory should exist"

    assert raw_dir.is_dir(), "data/raw should be a directory"
    assert processed_dir.is_dir(), "data/processed should be a directory"
    assert consent_dir.is_dir(), "data/consent should be a directory"


def test_gitkeep_files_created(mocked_config, temp_project_root):
    """Test that .gitkeep files are created in each directory."""
    create_directories()

    raw_dir = temp_project_root / "data" / "raw"
    processed_dir = temp_project_root / "data" / "processed"
    consent_dir = temp_project_root / "data" / "consent"

    gitkeep_raw = raw_dir / ".gitkeep"
    gitkeep_processed = processed_dir / ".gitkeep"
    gitkeep_consent = consent_dir / ".gitkeep"

    assert gitkeep_raw.exists(), ".gitkeep should exist in data/raw"
    assert gitkeep_processed.exists(), ".gitkeep should exist in data/processed"
    assert gitkeep_consent.exists(), ".gitkeep should exist in data/consent"

    assert gitkeep_raw.is_file(), ".gitkeep in data/raw should be a file"
    assert gitkeep_processed.is_file(), ".gitkeep in data/processed should be a file"
    assert gitkeep_consent.is_file(), ".gitkeep in data/consent should be a file"

    # Verify .gitkeep files have content
    assert gitkeep_raw.read_text().strip() != "", ".gitkeep in data/raw should have content"
    assert gitkeep_processed.read_text().strip() != "", ".gitkeep in data/processed should have content"
    assert gitkeep_consent.read_text().strip() != "", ".gitkeep in data/consent should have content"


def test_directories_empty_except_gitkeep(mocked_config, temp_project_root):
    """Test that directories only contain the .gitkeep file."""
    create_directories()

    raw_dir = temp_project_root / "data" / "raw"
    processed_dir = temp_project_root / "data" / "processed"
    consent_dir = temp_project_root / "data" / "consent"

    # Check that only .gitkeep exists in each directory
    assert len(list(raw_dir.iterdir())) == 1, "data/raw should only contain .gitkeep"
    assert len(list(processed_dir.iterdir())) == 1, "data/processed should only contain .gitkeep"
    assert len(list(consent_dir.iterdir())) == 1, "data/consent should only contain .gitkeep"