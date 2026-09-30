"""
Pytest configuration and fixtures for the llmXive research pipeline.

This module sets up global test configuration including random seed pinning
for reproducibility and temporary directory fixtures for test data isolation.
"""

import os
import random
import time
import hashlib
import logging
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def set_random_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducibility across libraries.
    
    Args:
        seed: The random seed value to use.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: numpy and torch seeds are set in their respective test modules
    # to avoid importing heavy libraries in conftest if not needed.

def pytest_configure(config):
    """
    Pytest hook to configure global settings before tests run.
    
    Args:
        config: The pytest configuration object.
    """
    # Pin random seeds for reproducibility
    set_random_seed(42)
    
    # Log start of test session
    logging.info("Test session started with random seed pinned to 42")

def pytest_addoption(parser):
    """
    Pytest hook to add custom command-line options.
    
    Args:
        parser: The pytest option parser.
    """
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="run slow tests"
    )
    parser.addoption(
        "--data-dir",
        action="store",
        default=None,
        help="Path to custom data directory for tests"
    )

def pytest_sessionstart(session):
    """
    Pytest hook called at the beginning of test session.
    
    Args:
        session: The pytest session object.
    """
    logging.info(f"Test session started: {session}")

def pytest_sessionfinish(session, exitstatus):
    """
    Pytest hook called at the end of test session.
    
    Args:
        session: The pytest session object.
        exitstatus: The exit status of the test session.
    """
    logging.info(f"Test session finished with status: {exitstatus}")

@pytest.fixture(scope="session")
def temp_data_dir() -> Generator[Path, None, None]:
    """
    Fixture providing a temporary directory for test data.
    
    Yields:
        Path: A temporary directory path for storing test data.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="llmXive_test_data_"))
    try:
        yield temp_dir
    finally:
        # Cleanup after tests
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

@pytest.fixture(scope="session")
def temp_results_dir() -> Generator[Path, None, None]:
    """
    Fixture providing a temporary directory for test results.
    
    Yields:
        Path: A temporary directory path for storing test results.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="llmXive_test_results_"))
    try:
        yield temp_dir
    finally:
        # Cleanup after tests
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)