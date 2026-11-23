"""
tests/unit/test_utils.py

Unit tests for src/utils.py functionality.
Tests cover logging setup, directory creation, and file I/O helpers.
"""

import os
import json
import csv
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.utils import (
    get_logger,
    setup_logging,
    ensure_directories,
    write_json,
    read_json,
    write_csv,
    read_csv,
    safe_delete,
    handle_error,
    validate_file_exists
)


class TestEnsureDirectories:
    def test_creates_nested_dirs(self, tmp_path):
        """Test that ensure_directories creates nested parent directories."""
        target_dir = tmp_path / "level1" / "level2" / "level3"
        result = ensure_directories(target_dir)
        
        assert result.exists()
        assert result.is_dir()
        assert (tmp_path / "level1").exists()
    
    def test_uses_existing_dir(self, tmp_path):
        """Test that ensure_directories does nothing if dir exists."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        
        result = ensure_directories(existing_dir)
        
        assert result == existing_dir


class TestJsonIO:
    def test_write_and_read_json(self, tmp_path):
        """Test round-trip JSON writing and reading."""
        data = {"key": "value", "number": 42, "nested": {"a": 1}}
        file_path = tmp_path / "test.json"
        
        write_json(data, file_path)
        
        assert file_path.exists()
        read_data = read_json(file_path)
        
        assert read_data == data
    
    def test_read_nonexistent_json(self, tmp_path):
        """Test that read_json raises FileNotFoundError."""
        file_path = tmp_path / "missing.json"
        
        with pytest.raises(FileNotFoundError):
            read_json(file_path)


class TestCsvIO:
    def test_write_and_read_csv(self, tmp_path):
        """Test round-trip CSV writing and reading."""
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        file_path = tmp_path / "test.csv"
        
        write_csv(data, file_path)
        
        assert file_path.exists()
        read_data = read_csv(file_path)
        
        # CSV reads strings by default
        expected = [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"}
        ]
        assert read_data == expected
    
    def test_write_empty_csv(self, tmp_path):
        """Test writing an empty list creates an empty file."""
        file_path = tmp_path / "empty.csv"
        write_csv([], file_path)
        
        assert file_path.exists()
        assert file_path.stat().st_size == 0


class TestSafeDelete:
    def test_deletes_existing_file(self, tmp_path):
        """Test that safe_delete removes an existing file."""
        file_path = tmp_path / "delete_me.txt"
        file_path.write_text("content")
        
        result = safe_delete(file_path)
        
        assert result is True
        assert not file_path.exists()
    
    def test_returns_true_if_missing(self, tmp_path):
        """Test that safe_delete returns True if file doesn't exist."""
        file_path = tmp_path / "nonexistent.txt"
        
        result = safe_delete(file_path)
        
        assert result is True
    
    def test_handles_directory_delete_failure(self, tmp_path):
        """Test behavior when trying to delete a directory (should fail gracefully)."""
        dir_path = tmp_path / "directory"
        dir_path.mkdir()
        
        # safe_delete expects a file, but os.unlink on a dir raises IsADirectoryError
        # Our function catches OSError and returns False
        result = safe_delete(dir_path)
        
        assert result is False
        assert dir_path.exists()


class TestValidateFileExists:
    def test_validates_existing_file(self, tmp_path):
        """Test validation of an existing file."""
        file_path = tmp_path / "valid.txt"
        file_path.write_text("content")
        
        result = validate_file_exists(file_path)
        
        assert result == file_path
    
    def test_raises_on_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        file_path = tmp_path / "missing.txt"
        
        with pytest.raises(FileNotFoundError):
            validate_file_exists(file_path)
    
    def test_raises_on_directory(self, tmp_path):
        """Test that FileNotFoundError is raised if path is a directory."""
        dir_path = tmp_path / "not_a_file"
        dir_path.mkdir()
        
        with pytest.raises(FileNotFoundError):
            validate_file_exists(dir_path)


class TestLogging:
    def test_get_logger_returns_instance(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test_module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
    
    def test_setup_logging_configures_handlers(self, caplog):
        """Test that setup_logging adds handlers."""
        setup_logging(level=logging.DEBUG, log_file=None)
        
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0
        assert any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers)
    
    def test_handle_error_logs_message(self, caplog):
        """Test that handle_error logs the exception message."""
        with caplog.at_level(logging.ERROR):
            handle_error(ValueError("test error"), "Test Operation")
        
        assert "Test Operation failed" in caplog.text
        assert "ValueError" in caplog.text
