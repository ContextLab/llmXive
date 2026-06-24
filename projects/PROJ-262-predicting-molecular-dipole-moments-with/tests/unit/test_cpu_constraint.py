"""
Unit tests for the cpu_constraint utility.
"""

from __future__ import annotations

import os

import pytest

# Import the function from the newly created module.
from utils.cpu_constraint import enforce_cpu_limit

@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    """
    Ensure that environment variables are cleared before each test to avoid
    interference from the test runner.
    """
    for var in [
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ]:
        monkeypatch.delenv(var, raising=False)
    yield

def test_enforce_cpu_limit_sets_env_vars():
    """
    After calling ``enforce_cpu_limit`` the relevant thread‑control
    environment variables should be set to the requested core count.
    """
    enforce_cpu_limit(max_cores=2)

    for var in [
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ]:
        assert os.getenv(var) == "2", f"{var} was not set to '2'"

def test_enforce_cpu_limit_invalid_argument():
    """
    Passing a non‑positive integer should raise a ``ValueError``.
    """
    with pytest.raises(ValueError):
        enforce_cpu_limit(max_cores=0)