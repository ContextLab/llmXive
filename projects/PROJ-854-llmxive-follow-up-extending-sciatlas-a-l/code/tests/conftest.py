import os
import sys
import tempfile
import shutil
import random
import logging
import pytest
import numpy as np
import networkx as nx
from pathlib import Path

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global project root path (assuming code/ is the root for imports)
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.lib import config

@pytest.fixture(autouse=True)
def setup_test_environment():
    """
    Autouse fixture to configure the test environment.
    1. Sets random seeds for reproducibility.
    2. Temporarily overrides config paths to a temporary directory.
    """
    # 1. Seed Pinning
    SEED = 42
    random.seed(SEED)
    np.random.seed(SEED)
    if hasattr(os, 'seed'):
        os.seed(SEED)
    
    # Ensure environment variables for seeds are set if the config reads them
    os.environ['PYTHONHASHSEED'] = str(SEED)

    # 2. Temporary Directory Setup
    # We create a temporary root to avoid polluting the real data/ or artifacts/
    temp_root = tempfile.mkdtemp(prefix="llmxive_test_")
    original_data_dir = config.DATA_DIR
    original_artifacts_dir = config.ARTIFACTS_DIR
    
    # Update config paths to point to temp dirs for this test run
    # Note: Since config is a module, we modify the attributes directly
    # This is safe because we restore them in the teardown (yield)
    temp_data_dir = Path(temp_root) / "data"
    temp_artifacts_dir = Path(temp_root) / "artifacts"
    temp_data_dir.mkdir(parents=True, exist_ok=True)
    temp_artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Patch the config module's global path variables
    config.DATA_DIR = str(temp_data_dir)
    config.ARTIFACTS_DIR = str(temp_artifacts_dir)
    
    # Also update the base paths if the config object has them
    if hasattr(config, 'BASE_DIR'):
        config.BASE_DIR = temp_root
    if hasattr(config, 'PROCESSED_DIR'):
        config.PROCESSED_DIR = str(temp_data_dir / "processed")
        (Path(config.PROCESSED_DIR)).mkdir(parents=True, exist_ok=True)
    if hasattr(config, 'RAW_DIR'):
        config.RAW_DIR = str(temp_data_dir / "raw")
        (Path(config.RAW_DIR)).mkdir(parents=True, exist_ok=True)

    logger.info(f"Test environment seeded with {SEED}. Data dir: {config.DATA_DIR}")

    yield

    # Teardown: Restore original paths
    config.DATA_DIR = original_data_dir
    config.ARTIFACTS_DIR = original_artifacts_dir
    if hasattr(config, 'BASE_DIR'):
        config.BASE_DIR = PROJECT_ROOT
    
    # Cleanup temp directory
    try:
        shutil.rmtree(temp_root)
        logger.info(f"Cleaned up temp directory: {temp_root}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temp directory {temp_root}: {e}")

@pytest.fixture
def temp_data_dir(setup_test_environment):
    """
    Provides the path to the temporary data directory created for the test suite.
    Relies on the autouse setup_test_environment fixture.
    """
    return Path(config.DATA_DIR)

@pytest.fixture
def temp_artifacts_dir(setup_test_environment):
    """
    Provides the path to the temporary artifacts directory created for the test suite.
    Relies on the autouse setup_test_environment fixture.
    """
    return Path(config.ARTIFACTS_DIR)

@pytest.fixture
def sample_graph():
    """
    Creates a deterministic sample graph for testing clustering and bridging.
    Uses fixed seeds to ensure reproducibility.
    """
    G = nx.Graph()
    # Add nodes with fixed attributes
    nodes = [
        (1, {'title': 'Node A', 'citation_count': 10, 'primary_cluster': 1}),
        (2, {'title': 'Node B', 'citation_count': 20, 'primary_cluster': 1}),
        (3, {'title': 'Node C', 'citation_count': 5, 'primary_cluster': 2}),
        (4, {'title': 'Node D', 'citation_count': 15, 'primary_cluster': 2}),
        (5, {'title': 'Node E', 'citation_count': 30, 'primary_cluster': 1}), # Bridge candidate
    ]
    G.add_nodes_from(nodes)
    
    # Add edges
    edges = [
        (1, 2), # Cluster 1 internal
        (1, 5), # Cluster 1 internal
        (2, 5), # Cluster 1 internal
        (3, 4), # Cluster 2 internal
        (5, 3), # Bridge: Node 5 connects Cluster 1 and 2
    ]
    G.add_edges_from(edges)
    return G

@pytest.fixture
def sample_clusters():
    """
    Returns a dictionary mapping node_id to cluster_id for the sample graph.
    """
    return {1: 1, 2: 1, 3: 2, 4: 2, 5: 1}

@pytest.fixture
def mock_node_data():
    """
    Returns a list of mock node dictionaries suitable for ingestion tests.
    """
    return [
        {
            "id": "10.1000/test1",
            "title": "Test Paper One",
            "citation_count": 100,
            "author_ids": ["auth1"],
            "publication_year": 2023
        },
        {
            "id": "10.1000/test2",
            "title": "Test Paper Two",
            "citation_count": 50,
            "author_ids": ["auth2"],
            "publication_year": 2022
        }
    ]

@pytest.fixture(autouse=True)
def configure_paths(temp_data_dir, temp_artifacts_dir):
    """
    Ensures that any code relying on config paths uses the temporary directories.
    This is a secondary check to ensure robustness.
    """
    # Re-verify paths are set correctly by the autouse fixture
    assert Path(temp_data_dir).exists(), "Temp data dir must exist"
    assert Path(temp_artifacts_dir).exists(), "Temp artifacts dir must exist"
    yield