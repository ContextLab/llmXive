"""
Pytest configuration and fixtures.
"""
import sys
import os
import pytest
from pathlib import Path

# Add the code directory to the path for all tests
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_dir = Path(__file__).parent.parent / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    # Cleanup if necessary

@pytest.fixture
def sample_p_values():
    """Fixture providing sample p-values for testing."""
    return [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]

@pytest.fixture
def sample_effect_sizes():
    """Fixture providing sample effect sizes."""
    return {
        "preprint": [0.2, 0.4, 0.6, 0.8, 1.0],
        "journal": [0.25, 0.45, 0.65, 0.85, 1.05]
    }