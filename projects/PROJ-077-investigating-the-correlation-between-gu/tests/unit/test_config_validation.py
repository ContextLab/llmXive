import os
import tempfile
from pathlib import Path
import pytest

from config_validation import validate_directories, validate_input_files, validate_configuration

class TestValidateDirectories:
    def test_existing_directory(self, tmp_path):
        """Test that an existing directory passes validation."""
        result = validate_directories([str(tmp_path)])
        assert result is True

    def test_missing_directory_creation(self, tmp_path):
        """Test that a missing directory is created successfully."""
        new_dir = tmp_path / "new_subdir"
        assert not new_dir.exists()
        
        result = validate_directories([str(new_dir)])
        
        assert result is True
        assert new_dir.exists()

    def test_invalid_path_is_not_dir(self, tmp_path):
        """Test that a path that is a file, not a dir, fails."""
        file_path = tmp_path / "a_file.txt"
        file_path.touch()
        
        result = validate_directories([str(file_path)])
        
        assert result is False

class TestValidateInputFiles:
    def test_existing_file(self, tmp_path):
        """Test that an existing file passes validation."""
        file_path = tmp_path / "test.csv"
        file_path.touch()
        result = validate_input_files([str(file_path)])
        assert result is True

    def test_missing_file(self, tmp_path):
        """Test that a missing file fails validation."""
        missing_file = tmp_path / "missing.csv"
        result = validate_input_files([str(missing_file)])
        assert result is False

    def test_multiple_files_partial_missing(self, tmp_path):
        """Test that if one of multiple files is missing, validation fails."""
        existing = tmp_path / "exists.csv"
        existing.touch()
        missing = tmp_path / "missing.csv"
        
        result = validate_input_files([str(existing), str(missing)])
        assert result is False

class TestValidateConfiguration:
    def test_full_validation_success(self, monkeypatch, tmp_path):
        """Test full validation when all requirements are met."""
        # Mock INPUT_PATHS to point to tmp_path files
        mock_input_paths = {
            "microbiome": str(tmp_path / "microbiome.csv"),
            "cognitive": str(tmp_path / "cognitive.csv")
        }
        
        # Create the files
        Path(mock_input_paths["microbiome"]).touch()
        Path(mock_input_paths["cognitive"]).touch()
        
        # Mock the global variables in config_validation
        # We need to patch the import or the module's reference
        # Since we can't easily patch the imported module's global in a simple way without complex mocking,
        # we will rely on the logic that if INPUT_PATHS is not a dict or empty, it defaults to checking
        # standard files. To make this test robust, we will ensure the default check paths exist in tmp_path
        # and mock the global INPUT_PATHS to be empty so it falls back to defaults.
        
        # Actually, the function validate_configuration uses INPUT_PATHS from 'config'.
        # To make this test work without modifying the global state of 'config',
        # we will create the default expected files in the tmp_path and ensure the function
        # logic handles it.
        # However, the function checks "data/raw/microbiome_data.csv" etc. relative to cwd.
        # To test this properly, we would need to change cwd or mock Path.exists.
        # For this unit test, we will mock the validate_input_files function to return True
        # and validate_directories to return True to isolate the logic.
        
        import config_validation as cv_module
        
        original_validate_dirs = cv_module.validate_directories
        original_validate_files = cv_module.validate_input_files
        
        cv_module.validate_directories = lambda x: True
        cv_module.validate_input_files = lambda x: True
        
        try:
            result = validate_configuration()
            assert result is True
        finally:
            cv_module.validate_directories = original_validate_dirs
            cv_module.validate_input_files = original_validate_files

    def test_full_validation_failure(self, monkeypatch):
        """Test full validation when a check fails."""
        import config_validation as cv_module
        
        original_validate_dirs = cv_module.validate_directories
        original_validate_files = cv_module.validate_input_files
        
        cv_module.validate_directories = lambda x: False
        cv_module.validate_input_files = lambda x: True
        
        try:
            result = validate_configuration()
            assert result is False
        finally:
            cv_module.validate_directories = original_validate_dirs
            cv_module.validate_input_files = original_validate_files