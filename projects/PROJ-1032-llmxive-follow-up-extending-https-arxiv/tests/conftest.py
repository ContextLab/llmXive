"""Pytest configuration and shared fixtures."""
import pytest
import os
import sys
from pathlib import Path

# Ensure the src directory is in the path for imports
@pytest.fixture(autouse=True)
def add_src_to_path():
    src_root = Path(__file__).parent.parent / "src"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    return src_root
