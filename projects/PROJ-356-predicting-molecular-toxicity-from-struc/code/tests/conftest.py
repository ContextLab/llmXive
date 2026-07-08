"""
Pytest configuration and shared fixtures for the toxicity prediction pipeline.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the code directory is in the path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_root = Path(__file__).parent.parent
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    yield

@pytest.fixture
def test_data_dir():
    """Path to the test data directory."""
    return Path(__file__).parent / "data"

@pytest.fixture
def project_root():
    """Path to the project root."""
    return Path(__file__).parent.parent.parent
