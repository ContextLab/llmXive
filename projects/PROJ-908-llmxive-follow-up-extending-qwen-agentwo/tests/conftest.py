"""
Pytest configuration and global fixtures for llmXive project.

This file enforces the fixed random seed (42) requirement for all tests
to ensure deterministic and reproducible results.
"""
import os
import random
import sys
from pathlib import Path

import pytest

# Ensure reproducibility by setting global random seeds
# This runs before any test collection or execution
SEED = 42

def pytest_configure(config):
    """Configure pytest with fixed seed and project paths."""
    # Set global random seed
    random.seed(SEED)
    os.environ["PYTHONHASHSEED"] = str(SEED)
    
    # Attempt to set numpy seed if available
    try:
        import numpy as np
        np.random.seed(SEED)
    except ImportError:
        pass
    
    # Attempt to set torch seed if available
    try:
        import torch
        torch.manual_seed(SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(SEED)
    except ImportError:
        pass

@pytest.fixture(autouse=True)
def reset_seeds():
    """
    Autouse fixture to reset random seeds before each test.
    This ensures that state from one test does not leak into another.
    """
    random.seed(SEED)
    os.environ["PYTHONHASHSEED"] = str(SEED)
    try:
        import numpy as np
        np.random.seed(SEED)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(SEED)
    except ImportError:
        pass
    yield
    # Optional: Cleanup or verification can happen here

@pytest.fixture
def project_root():
    """Return the path to the project root directory."""
    return Path(__file__).parent.parent

@pytest.fixture
def data_processed_dir(project_root):
    """Return the path to the processed data directory."""
    return project_root / "data" / "processed"

@pytest.fixture
def data_raw_dir(project_root):
    """Return the path to the raw data directory."""
    return project_root / "data" / "raw"

@pytest.fixture
def code_dir(project_root):
    """Return the path to the code directory."""
    return project_root / "code"

@pytest.fixture
def oracle_graph_path(data_processed_dir):
    """Path to the generated oracle graph JSON."""
    return data_processed_dir / "oracle_graph.json"

@pytest.fixture
def extracted_rules_path(data_processed_dir):
    """Path to the generated extracted rules JSON."""
    return data_processed_dir / "extracted_rules.json"

@pytest.fixture
def divergence_report_path(data_processed_dir):
    """Path to the generated divergence report JSON."""
    return data_processed_dir / "divergence_report.json"
