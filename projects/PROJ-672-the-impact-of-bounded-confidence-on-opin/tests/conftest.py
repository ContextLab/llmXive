"""
Pytest configuration and fixtures for the project.
"""
import os
import sys
from pathlib import Path
import pytest
import numpy as np

# Add project root to path for imports
# Assuming this file is at tests/conftest.py, root is two levels up
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the root directory of the project."""
    return ROOT_DIR

@pytest.fixture(scope="session")
def data_dir(project_root: Path) -> Path:
    """Return the data directory."""
    return project_root / "data"

@pytest.fixture(scope="session")
def code_dir(project_root: Path) -> Path:
    """Return the code directory."""
    return project_root / "code"

@pytest.fixture(scope="function")
def fixed_seed() -> int:
    """
    Provide a fixed random seed for reproducibility in tests.
    This ensures deterministic behavior in tests involving randomness.
    """
    return 42

@pytest.fixture(autouse=True)
def set_random_seed(fixed_seed: int):
    """
    Automatically set random seeds before each test to ensure reproducibility.
    """
    np.random.seed(fixed_seed)
    os.environ['PYTHONHASHSEED'] = str(fixed_seed)
    # Note: If using other random libraries (e.g., random), seed them here too.

@pytest.fixture
def sample_network_data(fixed_seed: int):
    """
    Provide sample network data for testing network generation utilities.
    """
    np.random.seed(fixed_seed)
    n_nodes = 10
    adj_matrix = np.random.randint(0, 2, size=(n_nodes, n_nodes))
    adj_matrix = (adj_matrix + adj_matrix.T) // 2 # Symmetric
    np.fill_diagonal(adj_matrix, 0)
    return adj_matrix
