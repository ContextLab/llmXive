"""
Pytest configuration and shared fixtures for the project.
"""
import pytest
import os
import sys
from pathlib import Path

# Add project root to path
@pytest.fixture(scope="session", autouse=True)
def add_project_root():
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    yield
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))

@pytest.fixture
def sample_config():
    """
    Returns a minimal configuration dictionary for testing.
    """
    return {
        "system_size": 100,
        "disorder_strength": 1.0,
        "energy": 0.0,
        "num_realizations": 1,
        "random_seed": 42,
        "max_iterations": 100,
        "tolerance": 1e-4
    }
