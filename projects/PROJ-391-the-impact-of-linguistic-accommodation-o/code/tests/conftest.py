"""
Pytest configuration and fixtures for the llmXive research pipeline.

This module provides:
- Global random seed pinning for reproducibility (numpy, random, os, torch if available).
- Shared fixtures for temporary directories and test data paths.
- Configuration for test execution environment.
"""
import os
import random
import sys
import tempfile
from pathlib import Path
from typing import Generator

import numpy as np
import pytest

# Global seed value for reproducibility
# This ensures that all random operations in the pipeline are deterministic
SEED_VALUE = 42

@pytest.fixture(autouse=True)
def set_random_seed() -> Generator[None, None, None]:
    """
    Autouse fixture to set random seeds before every test.
    
    This ensures that all tests run with a deterministic random state,
    making test results reproducible across runs.
    
    Yields:
        None: Control returns to the test after seeds are set.
    """
    # Set seed for Python's random module
    random.seed(SEED_VALUE)
    
    # Set seed for NumPy
    np.random.seed(SEED_VALUE)
    
    # Set seed for OS-level random (if applicable)
    os.environ['PYTHONHASHSEED'] = str(SEED_VALUE)
    
    # Try to set seed for PyTorch if available (optional dependency)
    try:
        import torch
        torch.manual_seed(SEED_VALUE)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(SEED_VALUE)
    except ImportError:
        pass  # PyTorch not installed, skip
    
    yield
    
    # Optional: Reset or cleanup after test if needed
    # Currently not required for this project

@pytest.fixture
def seed_value() -> int:
    """
    Fixture that provides the global seed value.
    
    Returns:
        int: The fixed seed value used for reproducibility.
    """
    return SEED_VALUE

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Fixture that creates a temporary directory for test artifacts.
    
    The directory is automatically cleaned up after the test completes.
    
    Yields:
        Path: Path object pointing to the temporary directory.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def project_root() -> Path:
    """
    Fixture that returns the project root directory.
    
    Assumes the test is run from within the project tree.
    
    Returns:
        Path: Path to the project root.
    """
    # Traverse up to find the root (assuming 'code' is a subdirectory)
    current = Path(__file__).resolve()
    while not (current / 'code').exists() and current != current.parent:
        current = current.parent
    return current

@pytest.fixture
def data_raw_dir(project_root: Path) -> Path:
    """
    Fixture that returns the path to the raw data directory.
    
    Args:
        project_root (Path): The project root directory.
    
    Returns:
        Path: Path to the raw data directory.
    """
    return project_root / 'data' / 'raw'

@pytest.fixture
def data_processed_dir(project_root: Path) -> Path:
    """
    Fixture that returns the path to the processed data directory.
    
    Args:
        project_root (Path): The project root directory.
    
    Returns:
        Path: Path to the processed data directory.
    """
    return project_root / 'data' / 'processed'

@pytest.fixture
def outputs_dir(project_root: Path) -> Path:
    """
    Fixture that returns the path to the outputs directory.
    
    Args:
        project_root (Path): The project root directory.
    
    Returns:
        Path: Path to the outputs directory.
    """
    return project_root / 'outputs'

@pytest.fixture
def figures_dir(project_root: Path) -> Path:
    """
    Fixture that returns the path to the figures directory.
    
    Args:
        project_root (Path): The project root directory.
    
    Returns:
        Path: Path to the figures directory.
    """
    return project_root / 'outputs' / 'figures'

@pytest.fixture
def reports_dir(project_root: Path) -> Path:
    """
    Fixture that returns the path to the reports directory.
    
    Args:
        project_root (Path): The project root directory.
    
    Returns:
        Path: Path to the reports directory.
    """
    return project_root / 'outputs' / 'reports'

# Pytest configuration hooks
def pytest_configure(config: pytest.Config) -> None:
    """
    Pytest hook to configure the test environment.
    
    Args:
        config (pytest.Config): The pytest configuration object.
    """
    # Set environment variables for reproducibility at the start
    os.environ['PYTHONHASHSEED'] = str(SEED_VALUE)
    
    # Log the seed value for debugging purposes
    print(f"\n[pytest] Random seed set to: {SEED_VALUE}")