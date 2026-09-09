"""
Pytest configuration and shared fixtures for the project.

This file configures pytest to run tests within the project structure,
ensuring the `code/` directory is on the Python path for imports.
"""
import sys
import os
import pytest
from pathlib import Path

# Add the project root to the Python path so imports like `from config import ...` work
# This assumes the tests are run from the project root: `python -m pytest`
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

# Optional: Configure logging to capture logs during tests
@pytest.fixture(autouse=True)
def set_logging_level(caplog):
    """
    Automatically capture logs for all tests to prevent log spam in CI/CD
    while allowing debugging when verbose flags are used.
    """
    import logging
    logging.basicConfig(level=logging.INFO)

# Optional: Fixture for a temporary directory for output artifacts
@pytest.fixture
def temp_output_dir(tmp_path):
    """
    Provides a temporary directory for tests that need to write files.
    Returns the Path object.
    """
    return tmp_path
