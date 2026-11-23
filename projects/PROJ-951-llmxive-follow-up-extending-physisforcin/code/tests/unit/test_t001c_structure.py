"""
Unit tests for Task T001c directory structure creation.

Verifies that the required directories and __init__.py files are created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from create_t001c_structure import create_t001c_structure

class TestT001cStructure:
    """Tests for the T001c directory creation logic."""

    def test_creates_data_directories(self, tmp_path):
        """Verify that all required data directories are created."""
        # Arrange
        data_dirs = ["data/raw", "data/curated", "data/eval", "data/validation", "data/control"]
        
        # Act
        result = create_t001c_structure(tmp_path)
        
        # Assert
        assert result is True
        for dir_path in data_dirs:
            full_path = tmp_path / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} is not a directory"

    def test_creates_src_directories(self, tmp_path):
        """Verify that all required source directories are created."""
        # Arrange
        src_dirs = [
            "src/generation", "src/filtering", "src/training",
            "src/evaluation", "src/augmentation", "src/utils"
        ]
        
        # Act
        result = create_t001c_structure(tmp_path)
        
        # Assert
        assert result is True
        for dir_path in src_dirs:
            full_path = tmp_path / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} is not a directory"

    def test_creates_test_directories(self, tmp_path):
        """Verify that all required test directories are created."""
        # Arrange
        test_dirs = ["tests/unit", "tests/integration"]
        
        # Act
        result = create_t001c_structure(tmp_path)
        
        # Assert
        assert result is True
        for dir_path in test_dirs:
            full_path = tmp_path / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} is not a directory"

    def test_creates_init_files(self, tmp_path):
        """Verify that __init__.py files are created in Python package directories."""
        # Arrange
        result = create_t001c_structure(tmp_path)
        
        # Assert
        assert result is True
        
        # Check src directories
        src_dirs = ["src/generation", "src/filtering", "src/training", 
                   "src/evaluation", "src/augmentation", "src/utils"]
        for dir_path in src_dirs:
            init_file = tmp_path / dir_path / "__init__.py"
            assert init_file.exists(), f"__init__.py not found in {dir_path}"
        
        # Check tests directories
        test_dirs = ["tests/unit", "tests/integration"]
        for dir_path in test_dirs:
            init_file = tmp_path / dir_path / "__init__.py"
            assert init_file.exists(), f"__init__.py not found in {dir_path}"

    def test_handles_existing_directories(self, tmp_path):
        """Verify that existing directories are not overwritten or cause errors."""
        # Arrange
        # Pre-create a directory
        pre_created = tmp_path / "data" / "raw"
        pre_created.mkdir(parents=True)
        
        # Act
        result = create_t001c_structure(tmp_path)
        
        # Assert
        assert result is True
        assert pre_created.exists()

    def test_fails_on_invalid_base_path(self, tmp_path):
        """Verify that the function returns False when base path doesn't exist."""
        # Arrange
        non_existent = tmp_path / "non_existent_path"
        
        # Act
        result = create_t001c_structure(non_existent)
        
        # Assert
        assert result is False
