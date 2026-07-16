"""
Pytest configuration and fixtures.
"""
import os
import tempfile
import pytest

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir
