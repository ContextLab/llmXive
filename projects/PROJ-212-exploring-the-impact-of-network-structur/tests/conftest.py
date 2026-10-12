import pytest
import os
import sys
from pathlib import Path
import random
import numpy as np

# Add the code directory to the path so that project modules can be imported in tests
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

@pytest.fixture
def sample_graph():
    """Provide a sample graph for testing."""
    return {
        "id": "test_graph",
        "nodes": 10,
        "edges": [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (4, 5), (5, 6), (6, 7), (7, 8), (8, 9)
        ]
    }

@pytest.fixture(scope="session")
def temp_data_dir(tmp_path_factory):
    """Create a temporary directory for data files used in tests."""
    return tmp_path_factory.mktemp("data")

@pytest.fixture(autouse=True)
def deterministic_rng():
    """Set a deterministic random seed for each test to ensure reproducibility."""
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    # Yield control to the test; no teardown actions are required.
    yield