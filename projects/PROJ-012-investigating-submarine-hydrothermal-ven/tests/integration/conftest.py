"""
Shared fixtures for integration tests.

This file provides common fixtures used across integration tests,
including test data generators and temporary directories.
"""
import logging
import os
import tempfile
from pathlib import Path
from typing import Generator, Tuple
import pytest
import numpy as np
import pandas as pd

@pytest.fixture
def integration_test_logger():
    """Create a logger for integration tests."""
    logger = logging.getLogger("integration_tests")
    logger.setLevel(logging.DEBUG)
    
    # Create a handler that writes to stderr for visibility during tests
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger

@pytest.fixture
def temp_integration_output_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for integration test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_diversity_ph_data():
    """Generate sample diversity and pH data for testing."""
    np.random.seed(42)
    n_samples = 100
    
    ph = np.random.uniform(4.0, 9.0, n_samples)
    # Add some non-linearity for realistic testing
    diversity = 2.5 + 0.3 * ph - 0.05 * (ph - 6.5) ** 2 + np.random.normal(0, 0.2, n_samples)
    
    return pd.DataFrame({
        'sample_id': [f'sample_{i:03d}' for i in range(n_samples)],
        'pH': ph,
        'diversity_shannon': diversity,
        'diversity_simpson': diversity * 0.8  # Correlated but different scale
    })

@pytest.fixture
def clean_environment():
    """Ensure a clean environment for integration tests."""
    # Store original environment
    original_env = os.environ.copy()
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
