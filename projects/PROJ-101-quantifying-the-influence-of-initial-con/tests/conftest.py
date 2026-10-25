"""
Pytest configuration fixtures required for the project.

* ``seed`` – provides a deterministic random seed (42) used by the
  dummy reproducibility test.
* ``tmp_path`` – is a built‑in pytest fixture; no custom code needed.
"""

import pytest

@pytest.fixture
def seed():
    """Return a fixed random seed for reproducibility tests."""
    return 42