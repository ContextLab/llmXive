"""
Unit tests for the setup_data_dirs module.
Verifies that the data directory structure is created correctly.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from setup_data_dirs import create_directories, main
from config import get_project_root, get_raw_data_dir, get_processed_data_dir, get_consent_dir


class TestCreateDirectories:
    """Tests for the create_directories function."""

    def test_creates_missing_directories(self, tmp_path, monkeypatch):
        """Test that missing directories are created."""
        # Mock the config functions to use a temporary directory
        def mock_get_project_root():
            return tmp_path

        monkeypatch.setattr("setup_data_dirs.get_project_root", mock_get_project_root)
        
        # Mock the config functions to return specific paths under tmp_path
        def mock_get_raw_data_dir():
            return tmp_path / "data" / "raw"

        def mock_get_processed_data_dir():
            return tmp_path / "data" / "processed"

        def mock_get_consent_dir():
            return tmp_path / "data" / "consent"

        monkeypatch.setattr("setup_data_dirs.get_raw_data_dir", mock_get_raw_data_dir)
        monkeypatch.setattr("setup_data_dirs.get_processed_data_dir", mock_get_processed_data_dir)
        monkeypatch.setattr("setup_data_dirs.get_consent_dir", mock_get_consent_dir)

        # Run the function
        result = create_directories()

        # Assert that the directories were created
        assert result is True
        assert mock_get_raw_data_dir().exists()
        assert mock_get_processed_data_dir().exists()
        assert mock_get_consent_dir().exists()

    def test_skips_existing_directories(self, tmp_path, monkeypatch):
        """Test that existing directories are not recreated."""
        # Mock the config functions to use a temporary directory
        def mock_get_project_root():
            return tmp_path

        monkeypatch.setattr("setup_data_dirs.get_project_root", mock_get_project_root)

        # Create the directories beforehand
        raw_dir = tmp_path / "data" / "raw"
        processed_dir = tmp_path / "data" / "processed"
        consent_dir = tmp_path / "data" / "consent"

        raw_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        consent_dir.mkdir(parents=True, exist_ok=True)

        # Mock the config functions to return specific paths under tmp_path
        def mock_get_raw_data_dir():
            return raw_dir

        def mock_get_processed_data_dir():
            return processed_dir

        def mock_get_consent_dir():
            return consent_dir

        monkeypatch.setattr("setup_data_dirs.get_raw_data_dir", mock_get_raw_data_dir)
        monkeypatch.setattr("setup_data_dirs.get_processed_data_dir", mock_get_processed_data_dir)
        monkeypatch.setattr("setup_data_dirs.get_consent_dir", mock_get_consent_dir)

        # Run the function
        result = create_directories()

        # Assert that the function succeeded
        assert result is True
        # Assert that the directories still exist
        assert raw_dir.exists()
        assert processed_dir.exists()
        assert consent_dir.exists()

    def test_creates_parent_directories(self, tmp_path, monkeypatch):
        """Test that parent directories are created if they don't exist."""
        # Mock the config functions to use a temporary directory
        def mock_get_project_root():
            return tmp_path

        monkeypatch.setattr("setup_data_dirs.get_project_root", mock_get_project_root)

        # Mock the config functions to return specific paths under tmp_path
        # Ensure the 'data' parent directory doesn't exist
        raw_dir = tmp_path / "data" / "raw"
        processed_dir = tmp_path / "data" / "processed"
        consent_dir = tmp_path / "data" / "consent"

        def mock_get_raw_data_dir():
            return raw_dir

        def mock_get_processed_data_dir():
            return processed_dir

        def mock_get_consent_dir():
            return consent_dir

        monkeypatch.setattr("setup_data_dirs.get_raw_data_dir", mock_get_raw_data_dir)
        monkeypatch.setattr("setup_data_dirs.get_processed_data_dir", mock_get_processed_data_dir)
        monkeypatch.setattr("setup_data_dirs.get_consent_dir", mock_get_consent_dir)

        # Run the function
        result = create_directories()

        # Assert that the directories were created
        assert result is True
        assert raw_dir.exists()
        assert processed_dir.exists()
        assert consent_dir.exists()
        # Assert that the parent 'data' directory was created
        assert (tmp_path / "data").exists()


class TestMain:
    """Tests for the main function."""

    def test_main_returns_zero_on_success(self, tmp_path, monkeypatch, capsys):
        """Test that main returns 0 on success."""
        # Mock the config functions to use a temporary directory
        def mock_get_project_root():
            return tmp_path

        monkeypatch.setattr("setup_data_dirs.get_project_root", mock_get_project_root)

        # Mock the config functions to return specific paths under tmp_path
        def mock_get_raw_data_dir():
            return tmp_path / "data" / "raw"

        def mock_get_processed_data_dir():
            return tmp_path / "data" / "processed"

        def mock_get_consent_dir():
            return tmp_path / "data" / "consent"

        monkeypatch.setattr("setup_data_dirs.get_raw_data_dir", mock_get_raw_data_dir)
        monkeypatch.setattr("setup_data_dirs.get_processed_data_dir", mock_get_processed_data_dir)
        monkeypatch.setattr("setup_data_dirs.get_consent_dir", mock_get_consent_dir)

        # Run the main function
        result = main()

        # Assert that the result is 0
        assert result == 0

    def test_main_returns_one_on_failure(self, tmp_path, monkeypatch, capsys):
        """Test that main returns 1 on failure."""
        # Mock the create_directories to raise an exception
        def mock_create_directories():
            raise Exception("Test exception")

        monkeypatch.setattr("setup_data_dirs.create_directories", mock_create_directories)

        # Run the main function
        result = main()

        # Assert that the result is 1
        assert result == 1