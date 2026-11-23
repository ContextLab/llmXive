import os
import sys
import pytest
from pathlib import Path

def test_pytest_discovery():
    """Verify that pytest can discover this test file."""
    assert True

def test_src_path_fixture(add_src_to_path):
    """Verify that the conftest.py fixture adds src to path."""
    assert add_src_to_path is not None
    src_path = Path(add_src_to_path)
    assert src_path.exists()
    assert (src_path / "utils").exists()

def test_import_from_src(add_src_to_path):
    """Verify that we can import from src modules."""
    try:
        from src.utils.config import Config
        from src.environment.baselines import PurePursuitController
        from src.agents.dqn_agent import DQNAgent
    except ImportError as e:
        pytest.fail(f"Failed to import from src: {e}")
