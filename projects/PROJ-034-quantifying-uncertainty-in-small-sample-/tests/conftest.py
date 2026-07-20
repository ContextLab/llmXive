"""
Shared fixtures for pytest.
"""
import pytest
import numpy as np
import os
import sys
from pathlib import Path

# Add code directory to path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_path = Path(__file__).parent.parent / "code"
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    yield
    if str(code_path) in sys.path:
        sys.path.remove(str(code_path))

@pytest.fixture
def sample_data():
    """
    Generate a small sample dataset for testing.
    """
    np.random.seed(123)
    n = 30
    p = 2
    X = np.random.randn(n, p)
    beta_true = np.array([1.0, -1.0])
    y = X @ beta_true + np.random.randn(n) * 0.5
    return {"X": X, "y": y, "beta_true": beta_true}

@pytest.fixture
def small_sample_data():
    """
    Generate a very small sample dataset (N < 10) for edge case testing.
    """
    np.random.seed(456)
    n = 5
    p = 2
    X = np.random.randn(n, p)
    beta_true = np.array([1.0, 2.0])
    y = X @ beta_true + np.random.randn(n) * 0.5
    return {"X": X, "y": y, "beta_true": beta_true}
