"""
Verification test for the logger fix (T063a prerequisite fix).
Ensures setup_logger accepts batch_id keyword argument.
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from simulation.logger import setup_logger


def test_setup_logger_with_batch_id():
    """Test that setup_logger accepts batch_id keyword argument."""
    # This was the failing call in the execution log
    logger = setup_logger(batch_id="main_pipeline")
    assert logger is not None
    assert logger.batch_id == "main_pipeline"
    assert logger.name == "main_pipeline"


def test_setup_logger_with_name():
    """Test that setup_logger accepts positional name argument."""
    logger = setup_logger("test_name")
    assert logger is not None
    assert logger.name == "test_name"


def test_setup_logger_with_name_and_batch_id():
    """Test that setup_logger accepts both name and batch_id."""
    logger = setup_logger("test_name", batch_id="batch_123")
    assert logger is not None
    assert logger.name == "test_name"
    assert logger.batch_id == "batch_123"


def test_setup_logger_with_underscore_name():
    """Test that setup_logger accepts __name__ (common usage)."""
    logger = setup_logger(__name__)
    assert logger is not None
    assert logger.name == __name__
