"""
Pytest configuration and shared fixtures.
"""
import pytest
import random
import numpy as np

def pytest_configure(config):
    """Configure pytest-randomly and other settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )

@pytest.fixture(autouse=True)
def set_seed():
    """Ensure deterministic behavior for tests."""
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    yield
