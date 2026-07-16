"""Pytest configuration and shared fixtures."""

import os
import sys
import pytest
from pathlib import Path

# Add project root to path for imports
@pytest.fixture(autouse=True)
def add_to_path():
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield

# Shared fixtures can be added here for tests that need them
# Example:
# @pytest.fixture
# def sample_emg_signal():
#     return np.random.randn(10240)  # 10 seconds at 1024 Hz
