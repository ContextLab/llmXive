"""
Pytest configuration and fixtures.
"""
import os
import sys
from pathlib import Path

# Ensure the code directory is in the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

@pytest.fixture(scope="session", autouse=True)
def ensure_data_structure():
    """
    Automatically setup the data directory structure before any tests run.
    """
    from code.setup_data_dirs import setup_data_directories
    setup_data_directories()
    yield
    # Teardown if necessary (usually not for directory creation)