"""
Smoke test to verify pytest configuration and test discovery are working.
This file ensures that the conftest.py path injection is active and
that imports from the project's src directory function correctly.
"""
import os
import sys
import pytest
from pathlib import Path

def test_pytest_discovery():
    """Verify that this test file is discovered and executed by pytest."""
    assert True

def test_src_path_fixture():
    """
    Verify that the 'add_src_to_path' fixture successfully added the project root
    to sys.path, allowing imports from 'src' modules.
    """
    code_root = Path(__file__).parent.parent
    assert str(code_root) in sys.path, f"Project root {code_root} not in sys.path"

def test_import_from_src():
    """
    Verify that we can import a known module from the project structure.
    This validates the integration between pytest, conftest, and the project API.
    """
    try:
        from src.utils.config import Config
        from src.environment.baselines import PurePursuitController
        assert Config is not None
        assert PurePursuitController is not None
    except ImportError as e:
        pytest.fail(f"Failed to import from src modules: {e}")