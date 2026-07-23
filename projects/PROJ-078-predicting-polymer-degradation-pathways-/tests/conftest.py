"""
Pytest configuration and fixtures.
"""
import pytest
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def logger():
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger("test")

@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test outputs."""
    return tmp_path
