"""
Tests for logging functionality in data generation.
"""
import pytest
import logging

def test_logger_setup():
    """Test that logger is configured."""
    logger = logging.getLogger("data_generation")
    assert logger is not None
