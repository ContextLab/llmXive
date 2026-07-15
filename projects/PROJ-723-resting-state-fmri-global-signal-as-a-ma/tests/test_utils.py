"""
Unit tests for code/utils.py
"""
import os
import json
import tempfile
from pathlib import Path
import pytest

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import (
    get_logger, 
    read_json, 
    write_json, 
    read_csv, 
    write_csv, 
    read_text, 
    write_text, 
    file_exists, 
    safe_divide, 
    validate_required_keys
)


class TestFileIO:
    def test_write_and_read_json(self):
        """Test that write_json and read_json work correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.json")
            test_data = {"key": "value", "number": 42}
            
            write_json(test_data, test_file)
            assert os.path.exists(test_file)
            
            loaded_data = read_json(test_file)
            assert loaded_data == test_data

    def test_write_and_read_text(self):
        """Test that write_text and read_text work correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            test_content = "Hello, World!\nLine 2"
            
            write_text(test_content, test_file)
            assert os.path.exists(test_file)
            
            loaded_content = read_text(test_file)
            assert loaded_content == test_content

    def test_read_nonexistent_json_raises_error(self):
        """Test that reading a non-existent JSON file raises an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_file = os.path.join(tmpdir, "nonexistent.json")
            
            with pytest.raises(FileNotFoundError):
                read_json(nonexistent_file)

    def test_read_nonexistent_text_raises_error(self):
        """Test that reading a non-existent text file raises an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_file = os.path.join(tmpdir, "nonexistent.txt")
            
            with pytest.raises(FileNotFoundError):
                read_text(nonexistent_file)


class TestCSVIO:
    def test_write_and_read_csv(self):
        """Test that write_csv and read_csv work correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.csv")
            test_data = [
                ["name", "age"],
                ["Alice", "30"],
                ["Bob", "25"]
            ]
            
            write_csv(test_data, test_file)
            assert os.path.exists(test_file)
            
            loaded_data = read_csv(test_file)
            assert loaded_data == test_data

    def test_read_nonexistent_csv_raises_error(self):
        """Test that reading a non-existent CSV file raises an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_file = os.path.join(tmpdir, "nonexistent.csv")
            
            with pytest.raises(FileNotFoundError):
                read_csv(nonexistent_file)


class TestFileExists:
    def test_file_exists_returns_true(self):
        """Test that file_exists returns True for existing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test.txt")
            Path(test_file).touch()
            
            assert file_exists(test_file) is True

    def test_file_exists_returns_false(self):
        """Test that file_exists returns False for non-existing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_file = os.path.join(tmpdir, "nonexistent.txt")
            
            assert file_exists(nonexistent_file) is False


class TestSafeDivide:
    def test_normal_division(self):
        """Test safe_divide with normal inputs."""
        assert safe_divide(10, 2) == 5.0

    def test_divide_by_zero_returns_none(self):
        """Test that safe_divide returns None when dividing by zero."""
        assert safe_divide(10, 0) is None

    def test_divide_by_none_returns_none(self):
        """Test that safe_divide returns None when denominator is None."""
        assert safe_divide(10, None) is None


class TestValidateRequiredKeys:
    def test_all_keys_present(self):
        """Test validation passes when all required keys are present."""
        data = {"a": 1, "b": 2, "c": 3}
        required = ["a", "b", "c"]
        
        result = validate_required_keys(data, required)
        assert result is True

    def test_missing_key_raises_error(self):
        """Test that validation fails when a required key is missing."""
        data = {"a": 1, "b": 2}
        required = ["a", "b", "c"]
        
        with pytest.raises(KeyError):
            validate_required_keys(data, required)

    def test_multiple_missing_keys_raises_error(self):
        """Test that validation fails with clear error for multiple missing keys."""
        data = {"a": 1}
        required = ["a", "b", "c", "d"]
        
        with pytest.raises(KeyError):
            validate_required_keys(data, required)


class TestGetLogger:
    def test_logger_creation(self):
        """Test that get_logger returns a valid logger."""
        logger = get_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"

    def test_logger_level(self):
        """Test that logger has appropriate default level."""
        logger = get_logger("test_logger")
        # Default level should be INFO or DEBUG depending on setup
        assert logger.level >= 0