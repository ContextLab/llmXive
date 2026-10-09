"""
Integration test to verify that the top-level project directories exist.
"""

import os
import pytest

@pytest.mark.integration
def test_top_level_directories_exist():
    """
    Assert that the required top‑level directories are present in the repository.
    """
    required_dirs = ["code", "data", "tests"]
    for d in required_dirs:
        assert os.path.isdir(d), f"Required directory '{d}' does not exist"