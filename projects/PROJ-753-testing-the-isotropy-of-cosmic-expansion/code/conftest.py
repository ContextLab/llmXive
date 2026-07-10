"""
Pytest configuration and shared fixtures for the isotropy analysis project.

This file configures pytest behavior and provides fixtures for test isolation,
logging setup, and temporary data directories.
"""
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# Ensure the project root is in the path for imports
# This allows tests to import from `code/` module directly
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging for tests to avoid silent failures in I/O
# We use a file handler or a stream handler depending on verbosity
@pytest.fixture(autouse=True)
def setup_test_logging(caplog):
    """
    Configure logging for tests to capture INFO level logs.
    This ensures that logging statements in the code are visible during test runs.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[caplog.handler]
    )
    yield
    # Reset logger state if necessary
    logging.getLogger().handlers.clear()

@pytest.fixture
def temp_data_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test data artifacts.
    Ensures tests do not pollute the real `data/` directory.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Create standard subdirectories expected by the pipeline
        (tmp_path / "raw").mkdir(parents=True, exist_ok=True)
        (tmp_path / "processed").mkdir(parents=True, exist_ok=True)
        (tmp_path / "figures").mkdir(parents=True, exist_ok=True)
        yield tmp_path

@pytest.fixture
def project_root() -> Path:
    """Return the project root path."""
    return PROJECT_ROOT

@pytest.fixture
def test_config_path() -> Path:
    """Return the path to the project root for config lookups."""
    return PROJECT_ROOT
