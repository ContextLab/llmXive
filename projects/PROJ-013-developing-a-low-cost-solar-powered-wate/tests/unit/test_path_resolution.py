"""
Integration-style tests for path resolution utilities.
"""
import pytest
from pathlib import Path
import sys

code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils import get_project_root, get_data_dir, get_code_dir, get_tests_dir


def test_path_hierarchy():
    """Verify that the resolved paths maintain correct hierarchy."""
    root = get_project_root()
    data = get_data_dir()
    code = get_code_dir()
    tests = get_tests_dir()

    # Root should be parent of code
    assert code.parent == root or root in code.parents

    # Data and Tests should be siblings of Code under Root
    assert data.parent == root
    assert tests.parent == root


def test_subdirectory_resolution():
    """Verify subdirectory resolution works correctly."""
    raw_data = get_data_dir("raw")
    processed_data = get_data_dir("processed")

    assert str(raw_data).endswith("raw")
    assert str(processed_data).endswith("processed")
    assert raw_data.parent == processed_data.parent