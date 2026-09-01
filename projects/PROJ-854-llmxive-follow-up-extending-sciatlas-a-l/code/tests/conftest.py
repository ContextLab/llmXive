"""
Pytest configuration and shared fixtures for the llmXive Bridging Coefficient Analysis project.

This module provides:
- Global test environment setup (logging, random seeds)
- Temporary directory fixtures for data and artifacts isolation
- Mock data generators for unit/integration tests
- Path configuration utilities
"""

import os
import sys
import tempfile
import shutil
import random
import logging
import pytest
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
import networkx as nx
import pandas as pd

# Ensure project root is in path for imports during tests
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import project modules for mock data generation
try:
    from src.models.node import Node
    from src.models.graph_utils import louvain_cluster, calc_bridging
except ImportError as e:
    # If imports fail during conftest loading, provide minimal mocks
    # This allows pytest to collect tests even if source modules are missing
    Node = None
    louvain_cluster = None
    calc_bridging = None

# ============================================================================
# Global Configuration
# ============================================================================

TEST_RANDOM_SEED = 42

def _set_global_seeds(seed: int = TEST_RANDOM_SEED) -> None:
    """Set random seeds for reproducibility across libraries."""
    random.seed(seed)
    np.random.seed(seed)
    # Set torch seed if available (for embedding tests)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

# ============================================================================
# Session-scoped fixtures
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Session-scoped fixture to configure global test environment.
    
    - Sets random seeds for reproducibility
    - Configures logging level for tests
    - Ensures clean state at session start
    """
    # Set global seeds
    _set_global_seeds(TEST_RANDOM_SEED)
    
    # Configure logging for tests (suppress INFO/DEBUG noise)
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Silence specific noisy libraries
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    logging.getLogger('datasets').setLevel(logging.ERROR)
    logging.getLogger('transformers').setLevel(logging.ERROR)
    
    yield
    
    # Cleanup after session (if needed)
    pass

# ============================================================================
# Temporary Directory Fixtures
# ============================================================================

@pytest.fixture
def temp_data_dir(tmp_path: Path):
    """
    Creates a temporary directory for test data files.
    
    Yields a Path object pointing to a unique temporary directory.
    The directory is automatically cleaned up after the test.
    
    Usage:
        def test_something(temp_data_dir):
            data_file = temp_data_dir / "test.csv"
            data_file.write_text("col1,col2\n1,2")
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories matching project structure
    (data_dir / "raw").mkdir(exist_ok=True)
    (data_dir / "processed").mkdir(exist_ok=True)
    (data_dir / "logs").mkdir(exist_ok=True)
    
    yield data_dir

@pytest.fixture
def temp_artifacts_dir(tmp_path: Path):
    """
    Creates a temporary directory for test artifacts (results, plots).
    
    Yields a Path object pointing to a unique temporary directory.
    Automatically cleaned up after the test.
    """
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (artifacts_dir / "results").mkdir(exist_ok=True)
    (artifacts_dir / "plots").mkdir(exist_ok=True)
    
    yield artifacts_dir

@pytest.fixture
def temp_config_dir(tmp_path: Path):
    """
    Creates a temporary directory for test configuration files.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    yield config_dir

# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_graph() -> nx.Graph:
    """
    Creates a small, deterministic sample graph for testing.
    
    Graph structure:
    - 6 nodes: A, B, C, D, E, F
    - Two clusters: {A, B, C} and {D, E, F}
    - One bridging edge: C-D
    
    Returns:
        networkx.Graph: Sample graph with known topology
    """
    G = nx.Graph()
    
    # Add nodes
    nodes = ['A', 'B', 'C', 'D', 'E', 'F']
    G.add_nodes_from(nodes)
    
    # Add edges within cluster 1
    G.add_edges_from([
        ('A', 'B'),
        ('B', 'C'),
        ('A', 'C')
    ])
    
    # Add edges within cluster 2
    G.add_edges_from([
        ('D', 'E'),
        ('E', 'F'),
        ('D', 'F')
    ])
    
    # Add bridging edge
    G.add_edge('C', 'D')
    
    return G

@pytest.fixture
def sample_clusters() -> Dict[str, int]:
    """
    Returns a dictionary mapping node IDs to cluster assignments.
    
    Matches the structure of sample_graph:
    - Cluster 0: A, B, C
    - Cluster 1: D, E, F
    
    Returns:
        Dict[str, int]: Node-to-cluster mapping
    """
    return {
        'A': 0,
        'B': 0,
        'C': 0,
        'D': 1,
        'E': 1,
        'F': 1
    }

@pytest.fixture
def mock_node_data() -> List[Dict[str, Any]]:
    """
    Generates mock node data for testing ingestion and processing.
    
    Returns:
        List[Dict]: List of node dictionaries with required fields
    """
    return [
        {
            'id': '1',
            'title': 'Machine Learning Fundamentals',
            'citation_count': 150,
            'embedding_vector': np.random.rand(384).tolist(),
            'primary_cluster': 0,
            'topic_cluster': 0,
            'bridging_coefficient': 0.5
        },
        {
            'id': '2',
            'title': 'Deep Learning Applications',
            'citation_count': 200,
            'embedding_vector': np.random.rand(384).tolist(),
            'primary_cluster': 0,
            'topic_cluster': 1,
            'bridging_coefficient': 0.0
        },
        {
            'id': '3',
            'title': 'Quantum Computing Basics',
            'citation_count': 80,
            'embedding_vector': np.random.rand(384).tolist(),
            'primary_cluster': 1,
            'topic_cluster': 2,
            'bridging_coefficient': 0.25
        }
    ]

@pytest.fixture
def sample_dataframe(mock_node_data) -> pd.DataFrame:
    """
    Creates a pandas DataFrame from mock node data.
    
    Returns:
        pd.DataFrame: DataFrame with node records
    """
    return pd.DataFrame(mock_node_data)

# ============================================================================
# Path Configuration
# ============================================================================

@pytest.fixture
def configure_paths(temp_data_dir: Path, temp_artifacts_dir: Path):
    """
    Configures project paths for testing using temporary directories.
    
    This fixture:
    - Updates environment variables for data/artifacts paths
    - Returns a dictionary of configured paths
    
    Args:
        temp_data_dir: Temporary data directory fixture
        temp_artifacts_dir: Temporary artifacts directory fixture
    
    Returns:
        Dict[str, Path]: Configuration paths
    """
    config = {
        'data_dir': temp_data_dir,
        'raw_dir': temp_data_dir / 'raw',
        'processed_dir': temp_data_dir / 'processed',
        'logs_dir': temp_data_dir / 'logs',
        'artifacts_dir': temp_artifacts_dir,
        'results_dir': temp_artifacts_dir / 'results',
        'plots_dir': temp_artifacts_dir / 'plots',
    }
    
    # Set environment variables for config.py to pick up
    os.environ['TEST_DATA_DIR'] = str(temp_data_dir)
    os.environ['TEST_ARTIFACTS_DIR'] = str(temp_artifacts_dir)
    
    yield config
    
    # Cleanup environment variables
    os.environ.pop('TEST_DATA_DIR', None)
    os.environ.pop('TEST_ARTIFACTS_DIR', None)

# ============================================================================
# Additional Utility Fixtures
# ============================================================================

@pytest.fixture
def isolated_node_graph() -> nx.Graph:
    """
    Creates a graph with an isolated node (degree 0).
    
    Useful for testing edge cases in bridging coefficient calculation.
    
    Returns:
        nx.Graph: Graph with one isolated node
    """
    G = nx.Graph()
    G.add_nodes_from(['A', 'B', 'C', 'isolated'])
    G.add_edges_from([('A', 'B'), ('B', 'C')])
    return G

@pytest.fixture
def single_node_cluster_graph() -> nx.Graph:
    """
    Creates a graph where one cluster has only a single node.
    
    Returns:
        nx.Graph: Graph with a singleton cluster
    """
    G = nx.Graph()
    G.add_nodes_from(['A', 'B', 'C', 'D'])
    G.add_edges_from([('A', 'B'), ('B', 'C'), ('C', 'D')])
    return G

@pytest.fixture
def complete_graph() -> nx.Graph:
    """
    Creates a complete graph (all nodes connected to all others).
    
    Returns:
        nx.Graph: Complete graph with 5 nodes
    """
    return nx.complete_graph(5)