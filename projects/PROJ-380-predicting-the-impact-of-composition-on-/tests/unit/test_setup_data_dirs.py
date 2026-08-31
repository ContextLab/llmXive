"""
Unit tests for the data directory setup functionality (T009).
Verifies that the required directory structure is created correctly.
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function to test
# We need to mock the config paths for testing in isolation
import sys
from unittest.mock import patch, MagicMock

from setup_data_dirs import setup_data_structure, main


class TestSetupDataDirs:
    """Tests for the data directory setup."""

    def test_directories_created(self, tmp_path):
        """Verify that raw, processed, and artifacts directories are created."""
        # Mock the get_paths function to return our temp directory
        mock_paths = {
            'data_root': str(tmp_path)
        }

        with patch('setup_data_dirs.get_paths', return_value=mock_paths):
            # Run the setup function
            setup_data_structure()

            # Verify the directories exist
            assert (tmp_path / 'raw').exists(), "raw directory not created"
            assert (tmp_path / 'processed').exists(), "processed directory not created"
            assert (tmp_path / 'artifacts').exists(), "artifacts directory not created"

    def test_gitkeep_files_created(self, tmp_path):
        """Verify that .gitkeep files are created in each subdirectory."""
        mock_paths = {
            'data_root': str(tmp_path)
        }

        with patch('setup_data_dirs.get_paths', return_value=mock_paths):
            setup_data_structure()

            # Verify .gitkeep files exist
            assert (tmp_path / 'raw' / '.gitkeep').exists(), ".gitkeep not created in raw"
            assert (tmp_path / 'processed' / '.gitkeep').exists(), ".gitkeep not created in processed"
            assert (tmp_path / 'artifacts' / '.gitkeep').exists(), ".gitkeep not created in artifacts"

    def test_main_function_success(self, tmp_path):
        """Verify that the main function runs without error."""
        mock_paths = {
            'data_root': str(tmp_path)
        }

        with patch('setup_data_dirs.get_paths', return_value=mock_paths):
            # This should not raise an exception
            main()

            # Verify directories were created
            assert (tmp_path / 'raw').exists()
            assert (tmp_path / 'processed').exists()
            assert (tmp_path / 'artifacts').exists()

    def test_idempotency(self, tmp_path):
        """Verify that running the setup twice doesn't cause errors."""
        mock_paths = {
            'data_root': str(tmp_path)
        }

        with patch('setup_data_dirs.get_paths', return_value=mock_paths):
            # Run twice
            setup_data_structure()
            setup_data_structure()

            # Verify directories still exist
            assert (tmp_path / 'raw').exists()
            assert (tmp_path / 'processed').exists()
            assert (tmp_path / 'artifacts').exists()