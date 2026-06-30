"""
Unit tests for code/utils.py utility functions.
"""

import pytest
import os
import tempfile
import logging
import csv
from unittest.mock import patch

# Import the module under test
# Assuming the test runner is run from the project root or code is in PYTHONPATH
from code.utils import (
    setup_logging,
    write_simulation_results,
    format_error_message,
    ensure_directory,
    get_timestamp_filename
)


class TestSetupLogging:
    def test_console_handler_created(self):
        """Test that a console handler is created."""
        logger = setup_logging()
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_file_handler_created(self):
        """Test that a file handler is created when log_file is provided."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.log') as tmp:
            log_path = tmp.name
        
        try:
            logger = setup_logging(log_file=log_path)
            assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        finally:
            if os.path.exists(log_path):
                os.remove(log_path)

    def test_level_respected(self):
        """Test that the logging level is set correctly."""
        logger = setup_logging(level=logging.DEBUG)
        assert logger.level == logging.DEBUG


class TestWriteSimulationResults:
    def test_write_new_file(self):
        """Test writing to a new CSV file."""
        results = [
            {"seed": 1, "value": 10.5},
            {"seed": 2, "value": 20.5}
        ]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            path = tmp.name
        
        try:
            write_simulation_results(results, path)
            
            assert os.path.exists(path)
            with open(path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]['seed'] == '1'
                assert rows[0]['value'] == '10.5'
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_append_to_existing_file(self):
        """Test appending to an existing CSV file."""
        results = [
            {"seed": 1, "value": 10.5}
        ]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            path = tmp.name
        
        try:
            # Write initial
            write_simulation_results(results, path)
            
            # Append more
            more_results = [
                {"seed": 2, "value": 20.5}
            ]
            write_simulation_results(more_results, path)
            
            with open(path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                # Should have 2 rows now, header written once
                assert len(rows) == 2
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_empty_results_raises(self):
        """Test that writing empty results without fieldnames raises ValueError."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            path = tmp.name
        
        try:
            with pytest.raises(ValueError):
                write_simulation_results([], path)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_creates_directories(self):
        """Test that function creates output directories if they don't exist."""
        results = [{"seed": 1}]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "subdir", "nested", "out.csv")
            
            write_simulation_results(results, nested_path)
            assert os.path.exists(nested_path)


class TestFormatErrorMessage:
    def test_basic_formatting(self):
        """Test basic error formatting."""
        err = ValueError("Something went wrong")
        msg = format_error_message(err)
        assert "ValueError" in msg
        assert "Something went wrong" in msg

    def test_with_context(self):
        """Test formatting with context."""
        err = RuntimeError("Failed")
        msg = format_error_message(err, context="Simulation Step")
        assert "[Simulation Step]" in msg

    def test_with_traceback(self):
        """Test formatting includes traceback when requested."""
        try:
            1 / 0
        except ZeroDivisionError as e:
            msg = format_error_message(e, include_traceback=True)
            assert "Traceback" in msg
            assert "ZeroDivisionError" in msg


class TestEnsureDirectory:
    def test_creates_new_directory(self):
        """Test creating a new directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "new_dir")
            result = ensure_directory(new_dir)
            assert os.path.isdir(result)
            assert os.path.isabs(result)

    def test_returns_existing_directory(self):
        """Test returning an existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_directory(tmpdir)
            assert result == os.path.abspath(tmpdir)


class TestGetTimestampFilename:
    def test_default_extension(self):
        """Test default extension is .csv."""
        filename = get_timestamp_filename("test")
        assert filename.startswith("test_")
        assert filename.endswith(".csv")

    def test_custom_extension(self):
        """Test custom extension."""
        filename = get_timestamp_filename("data", extension=".json")
        assert filename.startswith("data_")
        assert filename.endswith(".json")