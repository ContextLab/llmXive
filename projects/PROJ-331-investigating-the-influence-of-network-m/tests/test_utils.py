"""
Unit tests for code/utils.py
"""
import pytest
import numpy as np
import json
import os
from pathlib import Path
import tempfile
import logging

# Import functions to test
from utils import (
    PipelineError, DataNotFoundError, ProcessingError, ConfigurationError,
    get_logger, log_error, safe_mkdir, safe_write_json, safe_read_json,
    safe_write_text, safe_read_text, save_npy, load_npy, compute_sha256,
    log_execution_time
)
from config import DATA_LOGS

class TestExceptions:
    def test_pipeline_error_instantiation(self):
        exc = PipelineError("Test message")
        assert str(exc) == "Test message"

    def test_data_not_found_error(self):
        exc = DataNotFoundError("Missing file")
        assert isinstance(exc, PipelineError)
        assert str(exc) == "Missing file"

class TestLogger:
    def test_get_logger_creates_handlers(self):
        logger = get_logger("test_logger_unique")
        assert len(logger.handlers) == 2  # File and Console
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_log_execution_time(self):
        logger = get_logger("test_time_logger")
        start = 0.0
        log_execution_time(logger, start, "test_op")
        # Just checking it doesn't crash and logs something
        # The actual log content is hard to assert in a unit test without capturing logs,
        # but we verify the function runs.

class TestSafeMkdir:
    def test_safe_mkdir_creates_dir(self, tmp_path):
        new_dir = tmp_path / "sub" / "nested"
        result = safe_mkdir(new_dir)
        assert result.exists()
        assert result.is_dir()

class TestJsonIO:
    def test_write_read_json(self, tmp_path):
        test_data = {"key": "value", "num": 42}
        path = tmp_path / "test.json"
        
        safe_write_json(test_data, path)
        assert path.exists()
        
        loaded = safe_read_json(path)
        assert loaded == test_data

    def test_read_missing_json(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            safe_read_json(tmp_path / "nonexistent.json")

class TestTextIO:
    def test_write_read_text(self, tmp_path):
        text = "Hello, World!"
        path = tmp_path / "test.txt"
        
        safe_write_text(text, path)
        assert path.exists()
        
        loaded = safe_read_text(path)
        assert loaded == text

    def test_read_missing_text(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            safe_read_text(tmp_path / "nonexistent.txt")

class TestNpyIO:
    def test_save_load_npy(self, tmp_path):
        arr = np.array([[1, 2], [3, 4]])
        path = tmp_path / "test.npy"
        
        save_npy(arr, path)
        assert path.exists()
        
        loaded = load_npy(path)
        assert np.array_equal(arr, loaded)

    def test_load_missing_npy(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_npy(tmp_path / "nonexistent.npy")

class TestSha256:
    def test_compute_sha256(self, tmp_path):
        content = b"test content"
        path = tmp_path / "file.txt"
        path.write_bytes(content)
        
        hash_val = compute_sha256(path)
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64  # SHA256 hex length
