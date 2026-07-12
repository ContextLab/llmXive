"""
Pytest configuration and fixtures for the llmXive Bridging Coefficient Analysis project.

This module provides:
1. Temporary data directories that are cleaned up after each test session.
2. Random seed pinning to ensure reproducible test results.
3. Common fixtures for graph and node data generation.
"""

import os
import sys
import tempfile
import shutil
import random
import logging
from pathlib import Path
from typing import Generator, Dict, Any

import pytest
import numpy as np
import networkx as nx

# Add the project root to the path if not already present
# This ensures imports like `from src.lib import config` work during tests
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.lib import config

# Configure logging for tests to avoid noise but allow debugging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# ----------------------------------------------------------------------
# Global Configuration Fixtures
# ----------------------------------------------------------------------

@pytest.fixture(autouse=True)
def setup_test_environment():
    """
    Autouse fixture to pin random seeds for reproducibility.
    Ensures that random, numpy, and os.environ (if applicable) are deterministic.
    """
    # Pin seeds
    random.seed(42)
    np.random.seed(42)
    
    # Yield control to the test
    yield
    
    # Teardown: Optional cleanup if needed, though seed pinning is stateless
    pass

@pytest.fixture(scope="session", autouse=True)
def configure_paths():
    """
    Override the config paths to point to a temporary directory for the session.
    This prevents tests from writing to the actual data/ or artifacts/ folders.
    """
    # Create a temporary root for this test session
    temp_root = tempfile.mkdtemp(prefix="llmxive_test_")
    
    # Override the config module's paths dynamically
    # Note: This relies on the config module being importable and having mutable attributes
    # If config uses constants at import time that cannot be changed, we might need to mock them.
    # For this implementation, we assume config has setters or we override the module vars.
    
    original_data_dir = config.DATA_DIR
    original_artifacts_dir = config.ARTIFACTS_DIR
    
    config.DATA_DIR = Path(temp_root) / "data"
    config.ARTIFACTS_DIR = Path(temp_root) / "artifacts"
    
    # Ensure directories exist
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    (config.DATA_DIR / "raw").mkdir(exist_ok=True)
    (config.DATA_DIR / "processed").mkdir(exist_ok=True)
    config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    
    yield config
    
    # Restore original paths after session
    config.DATA_DIR = original_data_dir
    config.ARTIFACTS_DIR = original_artifacts_dir
    
    # Cleanup temp directory
    try:
        shutil.rmtree(temp_root)
    except OSError:
        pass  # Ignore cleanup errors in teardown

# ----------------------------------------------------------------------
# Temporary Directory Fixtures
# ----------------------------------------------------------------------

@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """
    Provides a temporary directory for data files that is unique per test.
    The directory is automatically cleaned up by pytest's tmp_path fixture.
    
    Returns:
        Path: The path to the temporary data directory.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

@pytest.fixture
def temp_artifacts_dir(tmp_path: Path) -> Path:
    """
    Provides a temporary directory for artifacts that is unique per test.
    
    Returns:
        Path: The path to the temporary artifacts directory.
    """
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    return artifacts_dir

# ----------------------------------------------------------------------
# Data Generation Fixtures
# ----------------------------------------------------------------------

@pytest.fixture
def sample_graph() -> nx.Graph:
    """
    Creates a deterministic sample graph for testing clustering and bridging logic.
    Structure: Two clusters connected by a single bridge node.
    
    Cluster A: 0, 1, 2
    Cluster B: 3, 4, 5
    Bridge: Node 2 connects to Node 3.
    """
    G = nx.Graph()
    # Cluster A
    G.add_edges_from([(0, 1), (1, 2), (0, 2)])
    # Cluster B
    G.add_edges_from([(3, 4), (4, 5), (3, 5)])
    # Bridge connection
    G.add_edge(2, 3)
    return G

@pytest.fixture
def sample_clusters() -> Dict[int, int]:
    """
    Returns a deterministic cluster mapping corresponding to sample_graph.
    """
    return {
        0: 0, 1: 0, 2: 0,  # Cluster 0
        3: 1, 4: 1, 5: 1   # Cluster 1
    }

@pytest.fixture
def mock_node_data() -> list:
    """
    Returns a list of dictionaries representing mock node data for ingestion tests.
    """
    return [
        {"id": "1", "title": "Test Paper A", "citation_count": 10},
        {"id": "2", "title": "Test Paper B", "citation_count": 5},
        {"id": "3", "title": "Test Paper C", "citation_count": 20},
    ]