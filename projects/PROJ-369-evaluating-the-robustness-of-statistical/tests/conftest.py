import pytest
import os
import sys

@pytest.fixture(autouse=True)
def add_src_to_path():
    """Automatically add the project's code/src directory to sys.path for imports."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_path = os.path.join(root, "code", "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    yield
