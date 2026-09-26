import os
import random
import time
import hashlib
import logging
import sys
import pytest
from pathlib import Path

# Ensure reproducibility for all tests
def set_random_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

def pytest_configure(config):
    """Configure pytest with random seed pinning."""
    seed = config.getoption("--seed", default=42)
    set_random_seed(seed)
    logging.info(f"Random seed pinned to {seed} for reproducibility")

def pytest_addoption(parser):
    """Add command-line options for pytest."""
    parser.addoption(
        "--seed",
        action="store",
        default="42",
        help="Random seed for reproducibility (default: 42)"
    )

def pytest_sessionstart(session):
    """Session start hook to enforce seed pinning."""
    seed = session.config.getoption("--seed")
    set_random_seed(int(seed))
    logging.info(f"Session started with seed: {seed}")

def pytest_sessionfinish(session, exitstatus):
    """Session finish hook to log completion."""
    logging.info(f"Session finished with exit status: {exitstatus}")

@pytest.fixture
def temp_data_dir(tmp_path):
    """Provide a temporary data directory for tests."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir

@pytest.fixture
def temp_results_dir(tmp_path):
    """Provide a temporary results directory for tests."""
    results_dir = tmp_path / "results"
    results_dir.mkdir(exist_ok=True)
    return results_dir
