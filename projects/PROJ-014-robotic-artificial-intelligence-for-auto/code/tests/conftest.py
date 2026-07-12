import os
import sys
import pytest
from pathlib import Path

# Ensure the 'code' directory is in the Python path so imports like
# 'from src.utils.config import Config' work correctly during test discovery.
@pytest.fixture(autouse=True)
def add_src_to_path():
    code_root = Path(__file__).parent.parent
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    yield
    # Optional: cleanup if needed, though typically not required for path insertion

# Optional: Global fixture for test isolation if needed later
@pytest.fixture(scope="session")
def session_root():
    return Path(__file__).parent.parent
