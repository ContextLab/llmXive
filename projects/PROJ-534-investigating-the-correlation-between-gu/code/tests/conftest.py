"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import logging
from pathlib import Path

import pytest

# Ensure the project root is in the path for imports
@pytest.fixture(autouse=True)
def add_src_to_path():
    """Add the project root to sys.path to allow imports from src."""
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield
    # Cleanup not strictly necessary as sys.path is process-local,
    # but good practice in some contexts.
    # if str(project_root) in sys.path:
    #     sys.path.remove(str(project_root))

@pytest.fixture(autouse=True)
def setup_logging():
    """Configure basic logging for tests."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    yield
