"""
Pytest configuration and fixtures for llmXive research pipeline.

This module configures the test environment to ensure:
1. Reproducibility via global random seed pinning.
2. Correct path resolution for project artifacts.
3. Logging configuration for test runs.
"""
import os
import sys
import random
import numpy as np
import pytest
from pathlib import Path

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Reproducibility configuration
# This seed is used to ensure deterministic behavior for tests involving
# randomization (e.g., permutation tests, data shuffling, initialization).
# It must be consistent with the simulation parameters in config.yaml if applicable.
TEST_SEED = 42

def pytest_configure(config):
    """
    Hook executed at the start of the pytest session.
    Sets global seeds for reproducibility.
    """
    # Set Python's random seed
    random.seed(TEST_SEED)
    
    # Set NumPy's random seed
    np.random.seed(TEST_SEED)
    
    # Log the seed for transparency in test reports
    print(f"\n[Pytest Configuration] Global random seed set to: {TEST_SEED}\n")

@pytest.fixture(scope="session", autouse=True)
def set_seed_session():
    """
    Session-scoped fixture to ensure seeds are set before any tests run.
    This acts as a secondary safeguard against seed drift in complex test suites.
    """
    random.seed(TEST_SEED)
    np.random.seed(TEST_SEED)
    yield
    # Optionally reset or leave as is for determinism across runs
    
@pytest.fixture
def project_root():
    """Provides the absolute path to the project root directory."""
    return PROJECT_ROOT

@pytest.fixture
def data_dir(project_root):
    """Provides the path to the data directory."""
    return project_root / "data"

@pytest.fixture
def processed_data_dir(data_dir):
    """Provides the path to the processed data directory."""
    return data_dir / "processed"

@pytest.fixture
def results_dir(project_root):
    """Provides the path to the results directory."""
    return project_root / "data" / "results"

@pytest.fixture
def src_dir(project_root):
    """Provides the path to the source code directory."""
    return project_root / "code" / "src"

@pytest.fixture
def config_path(project_root):
    """Provides the path to the config.yaml file."""
    return project_root / "code" / "config.yaml"

@pytest.fixture
def tmp_output_dir(tmp_path):
    """
    Provides a temporary directory for test outputs.
    Useful for testing file I/O without polluting the real data/ directories.
    """
    return tmp_path