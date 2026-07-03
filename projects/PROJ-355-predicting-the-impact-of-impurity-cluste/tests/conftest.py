"""
Pytest configuration and shared fixtures for all tests.
"""
import os
import sys
import pytest
from pathlib import Path

# Add project root to path for imports if running from tests directory
@pytest.fixture(autouse=True)
def add_src_to_path():
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Ensure code directory is accessible
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

    yield
