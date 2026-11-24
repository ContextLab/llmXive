"""
tests/conftest.py
-----------------
Pytest fixtures used across the test suite.
"""

import numpy as np
import pytest

@pytest.fixture(scope="session")
def seed():
    """Global deterministic seed for reproducibility."""
    return 42

@pytest.fixture
def tmp_path_factory(tmp_path_factory):
    """Expose the built‑in ``tmp_path_factory`` fixture."""
    return tmp_path_factory