"""
Pytest configuration and fixtures for the llmXive Bridging Coefficient Analysis project.

This module provides:
- Global random seed pinning for reproducibility.
- Temporary data directories that are cleaned up after tests.
- Fixtures to access project paths and configuration.
"""
import os
import random
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Import project config to ensure paths are consistent
# We assume the project structure is src/lib/config.py based on T004
# If src is not in sys.path, we add it
import sys
from pathlib import Path

# Ensure the 'src' directory is in the path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Attempt to import config; if it fails, we define a minimal fallback
# This ensures tests can run even if T004 hasn't been fully integrated yet,
# though T004 is marked as completed.
try:
    from lib.config import DATA_DIR, ARTIFACTS_DIR, RANDOM_SEED
except ImportError:
    # Fallback defaults if config.py is missing or import fails
    # This should not happen in a healthy repo, but prevents test crashes
    RANDOM_SEED = 42
    DATA_DIR = project_root / "data"
    ARTIFACTS_DIR = project_root / "artifacts"


def pytest_configure(config):
    """
    Configure pytest at startup.
    Sets the global random seed for reproducibility.
    """
    seed = config.getoption("--seed") if config.getoption("--seed") is not None else RANDOM_SEED
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


@pytest.fixture(scope="session")
def seed():
    """Return the global random seed."""
    return RANDOM_SEED


@pytest.fixture(scope="function")
def temp_data_dir(tmp_path):
    """
    Create a temporary directory for data processing within the test.
    Yields a Path object pointing to a temporary subdirectory named 'test_data'.
    Ensures isolation between tests.
    """
    test_data_dir = tmp_path / "test_data"
    test_data_dir.mkdir(parents=True, exist_ok=True)
    yield test_data_dir
    # Cleanup is handled automatically by tmp_path fixture, but explicit removal
    # ensures no lingering files if the test logic modifies the tmp_path structure deeply.
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir)


@pytest.fixture(scope="function")
def temp_artifact_dir(tmp_path):
    """
    Create a temporary directory for artifact generation within the test.
    Yields a Path object pointing to a temporary subdirectory named 'test_artifacts'.
    """
    test_artifact_dir = tmp_path / "test_artifacts"
    test_artifact_dir.mkdir(parents=True, exist_ok=True)
    yield test_artifact_dir
    if test_artifact_dir.exists():
        shutil.rmtree(test_artifact_dir)


@pytest.fixture(scope="function")
def sample_graph_dir(temp_data_dir):
    """
    Creates a minimal sample graph structure in the temp directory for testing ingestion.
    Returns the path to the directory containing the sample graph.
    """
    # This fixture prepares a known state for ingestion tests without hitting the network
    # or relying on external data files that might not exist.
    sample_file = temp_data_dir / "sample_graph.json"
    # Writing a minimal valid JSON structure for a graph
    import json
    sample_data = {
        "nodes": [
            {"id": "n1", "title": "Test Node 1", "citation_count": 10},
            {"id": "n2", "title": "Test Node 2", "citation_count": 20},
            {"id": "n3", "title": "Test Node 3", "citation_count": 5}
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"}
        ]
    }
    with open(sample_file, "w") as f:
        json.dump(sample_data, f)
    return temp_data_dir


# Pytest command line option for custom seed
def pytest_addoption(parser):
    parser.addoption(
        "--seed",
        action="store",
        default=RANDOM_SEED,
        type=int,
        help="Random seed for reproducibility (default: 42)"
    )
