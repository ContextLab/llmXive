"""
Pytest configuration and fixtures.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path for imports if running from test directory
@pytest.fixture(autouse=True)
def add_project_root():
    root = Path(__file__).parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
