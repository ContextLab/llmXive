"""
Pytest configuration and fixtures for the chaotic systems project.

This module provides shared fixtures for:
1. Random seed management to ensure reproducibility.
2. Temporary data directories for isolated test execution (via pytest's built‑in tmp_path fixture).
"""

import os
import sys
import pytest
import numpy as np
from pathlib import Path

# Ensure the project root is on sys.path so that imports from the
# `code/` package work in tests that need them.
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture
def seed() -> int:
    """
    Fixture providing a fixed random seed for reproducibility.
    Returns the constant value 42 as required by the specification.
    """
    return 42

@pytest.fixture(autouse=True)
def set_numpy_seed(seed: int) -> None:
    """
    Autouse fixture that sets NumPy's random seed before each test.
    Guarantees that any code using `np.random` starts from the same state.
    """
    np.random.seed(seed)

@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """
    Fixture creating a temporary directory structure mirroring the
    project's data layout.  Tests can write files here without affecting
    the real `data/` directory.

    Returns:
        Path: Path to the temporary data directory.
    """
    # Create subdirectories expected by some tests
    (tmp_path / "raw").mkdir(parents=True, exist_ok=True)
    (tmp_path / "processed").mkdir(parents=True, exist_ok=True)
    (tmp_path / "state").mkdir(parents=True, exist_ok=True)
    return tmp_path