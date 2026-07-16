import os
import tempfile
from pathlib import Path
import pytest

# Import the function to test
from utils.setup_data_dirs import create_data_directories


class TestDataDirectoryCreation:
    """Tests for the create_data_directories function."""

    def test_creates_raw_directory(self, tmp_path):
        """Test that data/raw directory is created."""
        # Arrange
        raw_dir = tmp_path / "data" / "raw"
        
        # Act
        create_data_directories(tmp_path)
        
        # Assert
        assert raw_dir.exists()
        assert raw_dir.is_dir()

    def test_creates_processed_directory(self, tmp_path):
        """Test that data/processed directory is created."""
        # Arrange
        processed_dir = tmp_path / "data" / "processed"
        
        # Act
        create_data_directories(tmp_path)
        
        # Assert
        assert processed_dir.exists()
        assert processed_dir.is_dir()

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        # Arrange - start with an empty tmp_path
        assert not (tmp_path / "data").exists()
        
        # Act
        create_data_directories(tmp_path)
        
        # Assert
        assert (tmp_path / "data").exists()
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()

    def test_idempotent_creation(self, tmp_path):
        """Test that calling the function multiple times doesn't cause errors."""
        # Act - call twice
        create_data_directories(tmp_path)
        create_data_directories(tmp_path)
        
        # Assert
        assert (tmp_path / "data" / "raw").exists()
        assert (tmp_path / "data" / "processed").exists()

    def test_directories_are_empty_after_creation(self, tmp_path):
        """Test that created directories are initially empty."""
        # Act
        create_data_directories(tmp_path)
        
        # Assert
        raw_dir = tmp_path / "data" / "raw"
        processed_dir = tmp_path / "data" / "processed"
        
        assert len(list(raw_dir.iterdir())) == 0
        assert len(list(processed_dir.iterdir())) == 0
