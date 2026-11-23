"""
Unit tests for the directory setup functionality.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from code.utils.setup_directories import setup_directories


class TestSetupDirectories:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        # Cleanup after test
        shutil.rmtree(temp_path)

    def test_creates_raw_directory(self, temp_dir):
        """Test that the raw directory is created."""
        data_path = os.path.join(temp_dir, "data")
        setup_directories(data_path)

        raw_path = os.path.join(data_path, "raw")
        assert os.path.isdir(raw_path), f"Directory {raw_path} was not created"

    def test_creates_processed_directory(self, temp_dir):
        """Test that the processed directory is created."""
        data_path = os.path.join(temp_dir, "data")
        setup_directories(data_path)

        processed_path = os.path.join(data_path, "processed")
        assert os.path.isdir(processed_path), f"Directory {processed_path} was not created"

    def test_creates_results_directory(self, temp_dir):
        """Test that the results directory is created."""
        data_path = os.path.join(temp_dir, "data")
        setup_directories(data_path)

        results_path = os.path.join(data_path, "results")
        assert os.path.isdir(results_path), f"Directory {results_path} was not created"

    def test_creates_all_directories_at_once(self, temp_dir):
        """Test that all directories are created in a single call."""
        data_path = os.path.join(temp_dir, "data")
        setup_directories(data_path)

        raw_path = os.path.join(data_path, "raw")
        processed_path = os.path.join(data_path, "processed")
        results_path = os.path.join(data_path, "results")

        assert os.path.isdir(raw_path)
        assert os.path.isdir(processed_path)
        assert os.path.isdir(results_path)

    def test_existent_directory_handling(self, temp_dir):
        """Test that existing directories are handled gracefully."""
        data_path = os.path.join(temp_dir, "data")
        # Create one directory beforehand
        os.makedirs(os.path.join(data_path, "raw"), exist_ok=True)

        # Should not raise an error
        setup_directories(data_path)

        assert os.path.isdir(os.path.join(data_path, "raw"))
        assert os.path.isdir(os.path.join(data_path, "processed"))
        assert os.path.isdir(os.path.join(data_path, "results"))

    def test_nested_directory_creation(self, temp_dir):
        """Test that parent directories are created if they don't exist."""
        data_path = os.path.join(temp_dir, "deeply", "nested", "data")
        setup_directories(data_path)

        raw_path = os.path.join(data_path, "raw")
        assert os.path.isdir(raw_path)
        assert os.path.isdir(os.path.join(data_path, "processed"))
        assert os.path.isdir(os.path.join(data_path, "results"))
