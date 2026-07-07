"""
Pytest configuration and fixtures.
"""
import pytest
import logging
from pathlib import Path

from code.utils import setup_logging

@pytest.fixture(scope="session", autouse=True)
def setup_test_logging():
    """Configure logging for test sessions."""
    logger = setup_logging()
    logger.info("Test session started")
    yield
    logger.info("Test session completed")

@pytest.fixture
def raw_data_dir():
    """Fixture for raw data directory path."""
    return Path("data/raw")

@pytest.fixture
def results_dir():
    """Fixture for results directory path."""
    return Path("results")
