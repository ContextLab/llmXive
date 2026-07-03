"""
Base test fixtures and seed management for the llmXive project.

This module provides pytest fixtures for:
- Global random seed management for reproducibility
- Logging configuration for test runs
- Common test utilities
"""
import logging
import os
import random
import sys
from pathlib import Path
from typing import Generator

import numpy as np
import pytest

# Ensure the code directory is in the path for imports
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))


@pytest.fixture(scope="session", autouse=True)
def set_seed() -> Generator[None, None, None]:
    """
    Fixture to set global random seeds for reproducibility.
    
    Sets seeds for:
    - Python's random module
    - NumPy's random generator
    
    This runs once per session and ensures deterministic behavior
    across test runs.
    """
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    
    # Yield control to tests
    yield
    
    # Optional: cleanup if needed
    pass


@pytest.fixture
def test_logger() -> logging.Logger:
    """
    Fixture providing a configured logger for test modules.
    
    Uses standard library logging with a StreamHandler to output
    to stderr during test execution. Configured to INFO level.
    
    Returns:
        logging.Logger: A logger instance named 'test_<module_name>'
    """
    module_name = os.getenv("PYTEST_CURRENT_TEST", "unknown_test")
    logger_name = f"test_{module_name.split('::')[0].replace('/', '_')}"
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers if fixture is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """
    Fixture providing a temporary directory for data artifacts.
    
    Creates a temporary directory structure mimicking the project's
    data layout for isolated test execution.
    
    Args:
        tmp_path: Pytest's built-in temporary directory path
    
    Returns:
        Path: The temporary directory path
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


@pytest.fixture
def sample_config_dict() -> dict:
    """
    Fixture providing a sample configuration dictionary.
    
    Returns a minimal valid configuration structure that can be
    passed to SimulationConfig or similar classes for testing.
    
    Returns:
        dict: A sample configuration dictionary
    """
    return {
        "n_samples": 100,
        "n_features": 5,
        "distribution": "normal",
        "mean_diff": 0.0,
        "std_dev": 1.0,
        "seed": 42,
        "scaling_methods": ["standardize", "minmax", "robust"],
        "test_alpha": 0.05,
        "n_iterations": 10
    }