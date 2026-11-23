"""
Pytest configuration and shared fixtures for llmXive tests.
"""
import os
import sys
from pathlib import Path

import pytest

# Ensure the code directory is in the path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_root = Path(__file__).parent.parent / "code"
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    yield
    if str(code_root) in sys.path:
        sys.path.remove(str(code_root))

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory for test outputs."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

@pytest.fixture
def sample_trajectory():
    """Provide a minimal valid trajectory structure for testing."""
    return {
        "trajectory_id": "test_001",
        "steps": [
            {"step_id": 1, "action": "open_app", "state": "home"},
            {"step_id": 2, "action": "click", "state": "app_open"}
        ]
    }