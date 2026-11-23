"""
Unit test to verify that the required top‑level project directories exist.
"""
import pytest
from pathlib import Path

@pytest.mark.parametrize("directory", ["code", "tests", "state"])
def test_directory_exists(directory):
    """Each of the core directories should be present."""
    assert Path(directory).is_dir(), f"Directory '{directory}' is missing"