"""
Unit tests for configuration validation logic.
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config_validation import validate_directories, validate_input_files, validate_configuration
from config import INPUT_PATHS

class TestValidateDirectories:
    def test_validate_directories_creates_missing(self, tmp_path):
        """Test that validate_directories creates missing directories."""
        # Mock the ensure_directories function to just return True
        with patch('config_validation.ensure_directories', return_value=None):
            # This should not raise an exception
            result = validate_directories()
            assert result is True

    def test_validate_directories_failure(self, tmp_path):
        """Test behavior when directory creation fails."""
        with patch('config_validation.ensure_directories', side_effect=PermissionError("Mock permission error")):
            result = validate_directories()
            assert result is False

class TestValidateInputFiles:
    def test_validate_input_files_all_exist_and_nonempty(self, tmp_path):
        """Test validation passes when all files exist and are non-empty."""
        # Create temporary files for each input path
        mock_paths = {}
        for key in INPUT_PATHS.keys():
            file_path = tmp_path / f"{key}.csv"
            file_path.write_text("col1,col2\n1,2\n") # Non-empty content
            mock_paths[key] = str(file_path)

        # Patch INPUT_PATHS to use our temp files
        with patch('config_validation.INPUT_PATHS', mock_paths):
            result = validate_input_files()
            assert result is True

    def test_validate_input_files_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised when a file is missing."""
        # Create only one file, leave others missing
        mock_paths = {}
        for i, key in enumerate(INPUT_PATHS.keys()):
            if i == 0:
                file_path = tmp_path / f"{key}.csv"
                file_path.write_text("data\n")
                mock_paths[key] = str(file_path)
            else:
                mock_paths[key] = str(tmp_path / "missing.csv") # This one won't exist

        with patch('config_validation.INPUT_PATHS', mock_paths):
            with pytest.raises(FileNotFoundError, match="Missing required input files"):
                validate_input_files()

    def test_validate_input_files_empty_file(self, tmp_path):
        """Test that ValueError is raised when a file is empty."""
        mock_paths = {}
        for i, key in enumerate(INPUT_PATHS.keys()):
            file_path = tmp_path / f"{key}.csv"
            if i == 0:
                file_path.write_text("") # Empty file
            else:
                file_path.write_text("data\n")
            mock_paths[key] = str(file_path)

        with patch('config_validation.INPUT_PATHS', mock_paths):
            with pytest.raises(ValueError, match="Empty required input files"):
                validate_input_files()

class TestValidateConfiguration:
    def test_validate_configuration_success(self, tmp_path):
        """Test full configuration validation passes."""
        # Setup temp files
        mock_paths = {}
        for key in INPUT_PATHS.keys():
            file_path = tmp_path / f"{key}.csv"
            file_path.write_text("col1,col2\n1,2\n")
            mock_paths[key] = str(file_path)

        with patch('config_validation.INPUT_PATHS', mock_paths):
            with patch('config_validation.ensure_directories', return_value=None):
                result = validate_configuration()
                assert result is True

    def test_validate_configuration_invalid_seed(self, tmp_path):
        """Test validation fails with invalid RANDOM_SEED."""
        mock_paths = {}
        for key in INPUT_PATHS.keys():
            file_path = tmp_path / f"{key}.csv"
            file_path.write_text("col1,col2\n1,2\n")
            mock_paths[key] = str(file_path)

        with patch('config_validation.INPUT_PATHS', mock_paths):
            with patch('config_validation.ensure_directories', return_value=None):
                with patch('config_validation.RANDOM_SEED', -1):
                    result = validate_configuration()
                    assert result is False

    def test_validate_configuration_invalid_sample_limit(self, tmp_path):
        """Test validation fails with invalid SAMPLE_LIMIT."""
        mock_paths = {}
        for key in INPUT_PATHS.keys():
            file_path = tmp_path / f"{key}.csv"
            file_path.write_text("col1,col2\n1,2\n")
            mock_paths[key] = str(file_path)

        with patch('config_validation.INPUT_PATHS', mock_paths):
            with patch('config_validation.ensure_directories', return_value=None):
                with patch('config_validation.SAMPLE_LIMIT', 0):
                    result = validate_configuration()
                    assert result is False