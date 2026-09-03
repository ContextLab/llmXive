"""
Pytest configuration and fixtures for the llmXive project.

This module provides:
1. A `random_seed` fixture to ensure reproducible random number generation.
2. A `tmp_data_dir` fixture to create and manage temporary directories for test data.
3. A `project_root` fixture to locate the project root directory.
"""
import os
import random
import tempfile
import shutil
from pathlib import Path
from typing import Generator

import numpy as np
import pytest

# Import project config to ensure consistency
from config import set_simulation_seed, get_full_config


@pytest.fixture(scope="session")
def project_root() -> Path:
    """
    Returns the root directory of the project.
    Assumes the test directory is `tests/` at the root level.
    """
    return Path(__file__).parent.parent


@pytest.fixture(scope="function")
def random_seed(request: pytest.FixtureRequest) -> int:
    """
    Fixture to set and return a random seed for reproducibility.
    Uses the `--seed` command line argument if provided, otherwise defaults to 42.
    Also sets the seed for numpy and the standard random module.

    Usage in tests:
        def test_something(random_seed):
            np.random.seed(random_seed) # Or rely on the fixture side effect
            ...
    """
    seed = request.config.getoption("--seed", default=42)
    
    # Ensure global reproducibility for this test run scope
    random.seed(seed)
    np.random.seed(seed)
    
    # Update project config if the simulation module relies on it
    try:
        set_simulation_seed(seed)
    except Exception:
        # Fallback if set_simulation_seed is not yet robust or requires specific config state
        pass
        
    return seed


@pytest.fixture(scope="function")
def tmp_data_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Fixture that creates a temporary directory for data artifacts during a test.
    This ensures tests do not pollute the actual `data/` or `data/raw/` directories.
    The directory is automatically cleaned up after the test.
    
    Yields:
        Path: The path to the temporary directory.
    """
    # Create a subdirectory structure mimicking the project data layout
    data_dir = tmp_path / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    state_dir = tmp_path / "state"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    
    yield tmp_path
    
    # Optional: Cleanup logic if shutil.rmtree is needed for specific reasons,
    # but tmp_path handles standard cleanup.
    # shutil.rmtree(tmp_path) 


# Command line argument for seed
def pytest_addoption(parser):
    parser.addoption(
        "--seed",
        action="store",
        default="42",
        help="Random seed for reproducible tests (default: 42)",
        type=int,
    )
