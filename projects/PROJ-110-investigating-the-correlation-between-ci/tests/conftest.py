"""
Pytest configuration and shared fixtures for PROJ-110.

This file sets up the test environment, including logging configuration,
temporary directories for data artifacts, and common mock objects.
"""

import os
import sys
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Generator, Optional

import pytest

# Ensure project code is importable
# The project root is expected to be the parent of 'code' and 'tests'
# We add the parent of the current file's directory (which is tests) to sys.path
# If running from project root, sys.path already includes '.'
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import setup_root_logger, get_logger


@pytest.fixture(scope="session", autouse=True)
def configure_logging() -> Generator[None, None, None]:
    """
    Configure logging for the entire test session.
    Sets up a root logger that outputs to console with a specific format.
    """
    # Create a unique log file for this session to avoid interleaving
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # Setup root logger
    setup_root_logger(
        level=logging.INFO,
        log_file=str(log_file),
        console=True
    )

    logger = get_logger("pytest_session")
    logger.info("Test session logging configured.")
    logger.info(f"Log file: {log_file}")

    yield

    logger.info("Test session finished.")


@pytest.fixture
def temp_data_dir() -> Generator[Path, None, None]:
    """
    Creates a temporary directory for test data artifacts.
    Ensures isolation between tests and cleans up after the test.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        data_dir = Path(tmp_dir)
        # Create standard subdirectories expected by the pipeline
        (data_dir / "raw").mkdir(exist_ok=True)
        (data_dir / "processed").mkdir(exist_ok=True)
        yield data_dir


@pytest.fixture
def sample_config_path(temp_data_dir) -> Path:
    """
    Creates a minimal valid configuration file for testing.
    """
    config_file = temp_data_dir / "config.yaml"
    config_content = {
        "project": {
            "id": "PROJ-110-test",
            "name": "Test Project"
        },
        "data": {
            "raw_dir": str(temp_data_dir / "raw"),
            "processed_dir": str(temp_data_dir / "processed")
        },
        "logging": {
            "level": "INFO"
        }
    }
    # Simple YAML dump without external dependency if yaml isn't strictly needed for the fixture,
    # but since utils.logging uses yaml, we assume it's available.
    # Using a simple string format to avoid circular import issues if yaml config is complex.
    with open(config_file, "w") as f:
        f.write(f"project:\n  id: PROJ-110-test\n  name: Test Project\n")
        f.write(f"data:\n  raw_dir: {temp_data_dir}/raw\n  processed_dir: {temp_data_dir}/processed\n")
        f.write(f"logging:\n  level: INFO\n")
    return config_file


@pytest.fixture
def mock_logger() -> logging.Logger:
    """
    Returns a logger instance configured for testing (no file output, console only).
    Useful for unit tests that need to inspect logs or just need a valid logger.
    """
    logger = logging.getLogger("test_mock_logger")
    logger.setLevel(logging.DEBUG)
    # Ensure no handlers are added to avoid duplicate logs in test output
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


@pytest.fixture
def project_root_path() -> Path:
    """
    Returns the path to the project root.
    """
    return project_root