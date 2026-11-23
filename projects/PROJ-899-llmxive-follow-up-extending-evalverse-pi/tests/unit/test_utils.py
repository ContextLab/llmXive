"""
Unit tests for utility functions.
"""
import os
import json
import csv
import tempfile
import logging
from pathlib import Path
import pytest
from src.utils import ensure_directories, write_json, read_json, write_csv, read_csv, safe_delete

class TestEnsureDirectories:
    def test_ensure_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = Path(tmpdir) / "nested" / "dir"
            ensure_directories(test_path)
            assert test_path.exists()

class TestJsonIO:
    def test_write_read_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            data = {"key": "value", "number": 42}
            write_json(data, test_file)
            loaded = read_json(test_file)
            assert loaded == data

class TestCsvIO:
    def test_write_read_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.csv"
            data = [{"col1": "a", "col2": 1}, {"col1": "b", "col2": 2}]
            write_csv(data, test_file)
            loaded = read_csv(test_file)
            assert len(loaded) == 2

class TestSafeDelete:
    def test_safe_delete_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test")
            assert safe_delete(test_file) == True
            assert not test_file.exists()

class TestValidateFileExists:
    def test_validate_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test")
            from src.utils import validate_file_exists
            assert validate_file_exists(test_file) == True

class TestLogging:
    def test_setup_logging(self):
        from src.utils import setup_logging
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = setup_logging(log_file)
            logger.info("Test message")
            assert log_file.exists()
