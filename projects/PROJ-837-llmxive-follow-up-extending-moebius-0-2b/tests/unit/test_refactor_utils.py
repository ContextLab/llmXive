"""
Unit tests for refactored utility functions (T039).

These tests verify the correctness of the cleanup and refactoring utilities
introduced in code/utils/refactor_utils.py.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from utils.refactor_utils import (
    RefactorError,
    PathValidationError,
    ensure_directory,
    safe_json_load,
    safe_json_save,
    validate_non_empty_list,
    validate_non_empty_dict,
    get_project_root,
    normalize_path,
    validate_required_keys,
    retry_on_failure
)

class TestEnsureDirectory:
    """Tests for ensure_directory function."""
    
    def test_creates_new_directory(self, tmp_path):
        """Test creating a new directory."""
        new_dir = tmp_path / "new" / "nested" / "dir"
        result = ensure_directory(new_dir)
        assert result.exists()
        assert result.is_dir()
    
    def test_existing_directory(self, tmp_path):
        """Test with existing directory."""
        result = ensure_directory(tmp_path)
        assert result == tmp_path
        assert result.is_dir()
    
    def test_invalid_path_fails(self, tmp_path):
        """Test that creating a file as a directory fails."""
        file_path = tmp_path / "file.txt"
        file_path.touch()
        with pytest.raises(PathValidationError):
            ensure_directory(file_path)

class TestSafeJsonLoad:
    """Tests for safe_json_load function."""
    
    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON file."""
        data = {"key": "value", "number": 42}
        file_path = tmp_path / "data.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        result = safe_json_load(file_path)
        assert result == data
    
    def test_file_not_found_with_default(self, tmp_path):
        """Test file not found with default value."""
        default = {"default": "value"}
        result = safe_json_load(tmp_path / "missing.json", default=default)
        assert result == default
    
    def test_file_not_found_no_default(self, tmp_path):
        """Test file not found without default raises error."""
        with pytest.raises(RefactorError):
            safe_json_load(tmp_path / "missing.json")
    
    def test_invalid_json(self, tmp_path):
        """Test invalid JSON content."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("not valid json")
        
        with pytest.raises(RefactorError):
            safe_json_load(file_path)

class TestSafeJsonSave:
    """Tests for safe_json_save function."""
    
    def test_save_valid_data(self, tmp_path):
        """Test saving valid data."""
        data = {"key": "value"}
        file_path = tmp_path / "output.json"
        
        safe_json_save(data, file_path)
        
        assert file_path.exists()
        with open(file_path, 'r') as f:
            loaded = json.load(f)
        assert loaded == data
    
    def test_creates_directories(self, tmp_path):
        """Test that save creates parent directories."""
        data = {"key": "value"}
        file_path = tmp_path / "nested" / "dir" / "output.json"
        
        safe_json_save(data, file_path)
        
        assert file_path.exists()

class TestValidateNonEmptyList:
    """Tests for validate_non_empty_list function."""
    
    def test_valid_list(self):
        """Test with a non-empty list."""
        items = [1, 2, 3]
        result = validate_non_empty_list(items, "test_field")
        assert result == items
    
    def test_empty_list_raises(self):
        """Test that empty list raises error."""
        with pytest.raises(RefactorError) as exc_info:
            validate_non_empty_list([], "test_field")
        assert "test_field" in str(exc_info.value)

class TestValidateNonEmptyDict:
    """Tests for validate_non_empty_dict function."""
    
    def test_valid_dict(self):
        """Test with a non-empty dictionary."""
        data = {"key": "value"}
        result = validate_non_empty_dict(data, "test_field")
        assert result == data
    
    def test_empty_dict_raises(self):
        """Test that empty dictionary raises error."""
        with pytest.raises(RefactorError) as exc_info:
            validate_non_empty_dict({}, "test_field")
        assert "test_field" in str(exc_info.value)

class TestGetProjectRoot:
    """Tests for get_project_root function."""
    
    def test_returns_path(self):
        """Test that function returns a Path object."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

class TestNormalizePath:
    """Tests for normalize_path function."""
    
    def test_absolute_path(self):
        """Test with an absolute path."""
        path = Path("/tmp/test")
        result = normalize_path(path)
        assert result.is_absolute()
    
    def test_relative_path(self):
        """Test with a relative path."""
        result = normalize_path("code/utils")
        assert result.is_absolute()
        assert result.exists()

class TestValidateRequiredKeys:
    """Tests for validate_required_keys function."""
    
    def test_all_keys_present(self):
        """Test when all required keys are present."""
        data = {"a": 1, "b": 2, "c": 3}
        result = validate_required_keys(data, ["a", "b"], "test")
        assert result == data
    
    def test_missing_key_raises(self):
        """Test when a required key is missing."""
        data = {"a": 1, "b": 2}
        with pytest.raises(RefactorError) as exc_info:
            validate_required_keys(data, ["a", "b", "c"], "test")
        assert "c" in str(exc_info.value)
        assert "test" in str(exc_info.value)

class TestRetryOnFailure:
    """Tests for retry_on_failure decorator."""
    
    def test_successful_function(self):
        """Test function that succeeds immediately."""
        @retry_on_failure(max_retries=3, delay=0.1)
        def success_func():
            return "success"
        
        result = success_func()
        assert result == "success"
    
    def test_function_fails_then_succeeds(self):
        """Test function that fails once then succeeds."""
        call_count = 0
        
        @retry_on_failure(max_retries=3, delay=0.01)
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary failure")
            return "success"
        
        result = flaky_func()
        assert result == "success"
        assert call_count == 2
    
    def test_function_always_fails(self):
        """Test function that always fails."""
        @retry_on_failure(max_retries=2, delay=0.01)
        def fail_func():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError):
            fail_func()
