import pytest
import sys
from pathlib import Path
from simulation.logger import setup_logger

class TestSetupLogger:
    def test_setup_logger_string(self):
        """Test setup_logger with string argument."""
        logger = setup_logger("test_name")
        assert logger is not None
        assert logger.name == "test_name"

    def test_setup_logger_batch_id(self):
        """Test setup_logger with batch_id keyword."""
        logger = setup_logger(batch_id="main_pipeline")
        assert logger is not None
        assert logger.batch_id == "main_pipeline"

    def test_setup_logger_module(self):
        """Test setup_logger with __name__."""
        logger = setup_logger(__name__)
        assert logger is not None

    def test_setup_logger_no_args(self):
        """Test setup_logger with no arguments."""
        logger = setup_logger()
        assert logger is not None

    def test_logger_log_method(self):
        """Test logger log method."""
        logger = setup_logger("test")
        entry = logger.log("operation", param="value")
        assert entry is not None
        assert entry.operation == "operation"
        assert entry.parameters["param"] == "value"

    def test_logger_to_json(self):
        """Test logger entry to_json."""
        logger = setup_logger("test")
        entry = logger.log("op")
        json_str = entry.to_json()
        assert isinstance(json_str, str)
        assert "op" in json_str
