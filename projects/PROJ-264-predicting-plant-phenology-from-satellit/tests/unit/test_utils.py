"""
Unit tests for src/lib/utils.py
"""
import json
import os
import tempfile
from pathlib import Path
import logging

import pandas as pd
import pytest
import yaml

# Import the module under test
# Ensure the path is set up correctly by conftest
from src.lib.utils import (
    setup_logging,
    set_random_seed,
    compute_file_checksum,
    ensure_directory,
    save_csv,
    load_csv,
    save_json,
    load_json,
    save_yaml,
    load_yaml,
)


class TestLogging:
    def test_setup_logging_console_only(self, caplog):
        """Test that logging works to console when no file is provided."""
        logger = setup_logging(log_file=None, level=logging.DEBUG)
        assert logger.level == logging.DEBUG
        # Reset handler count to avoid accumulation in tests
        logger.handlers = [h for h in logger.handlers if not isinstance(h, logging.FileHandler)]

        with caplog.at_level(logging.INFO):
            logger.info("Test message")
        assert "Test message" in caplog.text

    def test_setup_logging_with_file(self, tmp_path):
        """Test that logging writes to a file when provided."""
        log_file = tmp_path / "test.log"
        logger = setup_logging(log_file=log_file, level=logging.INFO)

        # Force flush
        for handler in logger.handlers:
            handler.flush()

        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" not in content  # No messages logged yet in this specific block context
        
        # Log something explicitly
        logger.info("File log test")
        for handler in logger.handlers:
            handler.flush()
        
        content = log_file.read_text()
        assert "File log test" in content


class TestRandomSeed:
    def test_set_random_seed(self):
        """Test that random seed sets state consistently."""
        set_random_seed(42)
        val1 = random.random()
        
        set_random_seed(42)
        val2 = random.random()
        
        assert val1 == val2
        
        # Also check numpy
        import numpy as np
        set_random_seed(42)
        arr1 = np.random.rand(5)
        
        set_random_seed(42)
        arr2 = np.random.rand(5)
        
        assert np.array_equal(arr1, arr2)


class TestChecksum:
    def test_compute_file_checksum(self, tmp_path):
        """Test checksum computation for a known file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World")
        
        checksum = compute_file_checksum(test_file)
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex length

    def test_compute_file_checksum_not_found(self):
        """Test that missing file raises error."""
        with pytest.raises(FileNotFoundError):
            compute_file_checksum("/nonexistent/path/file.txt")


class TestDirectory:
    def test_ensure_directory(self, tmp_path):
        """Test directory creation."""
        new_dir = tmp_path / "sub" / "deep"
        result = ensure_directory(new_dir)
        
        assert result.exists()
        assert result.is_dir()


class TestCSV:
    def test_save_and_load_csv(self, tmp_path):
        """Test CSV save and load."""
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        path = tmp_path / "data.csv"
        
        save_csv(df, path)
        assert path.exists()
        
        loaded_df = load_csv(path)
        pd.testing.assert_frame_equal(df, loaded_df)

    def test_load_csv_not_found(self):
        """Test CSV load error."""
        with pytest.raises(FileNotFoundError):
            load_csv("/nonexistent/file.csv")


class TestJSON:
    def test_save_and_load_json(self, tmp_path):
        """Test JSON save and load."""
        data = {"key": "value", "num": 123}
        path = tmp_path / "data.json"
        
        save_json(data, path)
        assert path.exists()
        
        loaded = load_json(path)
        assert loaded == data

    def test_load_json_not_found(self):
        """Test JSON load error."""
        with pytest.raises(FileNotFoundError):
            load_json("/nonexistent/file.json")


class TestYAML:
    def test_save_and_load_yaml(self, tmp_path):
        """Test YAML save and load."""
        data = {"config": {"setting": True, "list": [1, 2, 3]}}
        path = tmp_path / "data.yaml"
        
        save_yaml(data, path)
        assert path.exists()
        
        loaded = load_yaml(path)
        assert loaded == data

    def test_load_yaml_not_found(self):
        """Test YAML load error."""
        with pytest.raises(FileNotFoundError):
            load_yaml("/nonexistent/file.yaml")
