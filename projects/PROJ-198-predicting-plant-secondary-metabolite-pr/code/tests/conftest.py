"""
Pytest configuration and fixtures.
"""

import sys
from pathlib import Path

import pytest


# Add project root to path for imports
@pytest.fixture(autouse=True)
def add_src_to_path():
    src_path = Path(__file__).parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
