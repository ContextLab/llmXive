import os
import sys
import tempfile
import shutil
import random
import logging
import pytest
import numpy as np
import networkx as nx
import pandas as pd
from typing import List, Dict, Any, Generator
from pathlib import Path

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Global seed for reproducibility
TEST_SEED = 42

def pytest_configure(config):
    """Configure pytest with default settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment with fixed seeds and temporary directories."""
    # Set random seeds for reproducibility
    random.seed(TEST_SEED)
    np.random.seed(TEST_SEED)
    
    # Store original paths
    original_cwd = os.getcwd()
    
    # Create temporary directory for test data
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_data_dir = Path(tmp_dir)
        os.chdir(tmp_dir)
        
        # Set environment variables for test paths
        os.environ['TEST_DATA_DIR'] = str(test_data_dir)
        os.environ['DATA_DIR'] = str(test_data_dir / 'data')
        os.environ['ARTIFACTS_DIR'] = str(test_data_dir / 'artifacts')
        
        # Create required directories
        (test_data_dir / 'data' / 'raw').mkdir(parents=True, exist_ok=True)
        (test_data_dir / 'data' / 'processed').mkdir(parents=True, exist_ok=True)
        (test_data_dir / 'artifacts' / 'results').mkdir(parents=True, exist_ok=True)
        (test_data_dir / 'artifacts' / 'plots').mkdir(parents=True, exist_ok=True)
        (test_data_dir / 'data' / 'logs').mkdir(parents=True, exist_ok=True)
        
        try:
            yield {
                'temp_dir': Path(tmp_dir),
                'data_dir': Path(os.environ['DATA_DIR']),
                'artifacts_dir': Path(os.environ['ARTIFACTS_DIR'])
            }
        finally:
            # Restore original directory
            os.chdir(original_cwd)
            # Clear environment variables
            for key in ['TEST_DATA_DIR', 'DATA_DIR', 'ARTIFACTS_DIR']:
                if key in os.environ:
                    del os.environ[key]

@pytest.fixture
def temp_data_dir(setup_test_environment) -> Path:
    """Provide a temporary directory for data files."""
    return setup_test_environment['data_dir']

@pytest.fixture
def temp_artifacts_dir(setup_test_environment) -> Path:
    """Provide a temporary directory for artifacts."""
    return setup_test_environment['artifacts_dir']

@pytest.fixture
def temp_config_dir(setup_test_environment) -> Path:
    """Provide a temporary directory for config files."""
    config_dir = setup_test_environment['temp_dir'] / 'config'
    config_dir.mkdir(exist_ok=True)
    return config_dir

@pytest.fixture
def sample_graph() -> nx.Graph:
    """Create a sample graph for testing."""
    G = nx.Graph()
    # Add nodes with attributes
    G.add_node(1, title="Node 1", citation_count=10, embedding_vector=np.array([0.1, 0.2]), 
               primary_cluster=0, topic_cluster=0)
    G.add_node(2, title="Node 2", citation_count=20, embedding_vector=np.array([0.2, 0.3]), 
               primary_cluster=0, topic_cluster=1)
    G.add_node(3, title="Node 3", citation_count=30, embedding_vector=np.array([0.3, 0.4]), 
               primary_cluster=1, topic_cluster=0)
    G.add_node(4, title="Node 4", citation_count=40, embedding_vector=np.array([0.4, 0.5]), 
               primary_cluster=1, topic_cluster=1)
    
    # Add edges
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    G.add_edge(3, 4)
    G.add_edge(1, 4)
    
    return G

@pytest.fixture
def sample_clusters() -> Dict[int, int]:
    """Create sample cluster assignments."""
    return {
        1: 0,
        2: 0,
        3: 1,
        4: 1
    }

@pytest.fixture
def mock_node_data() -> List[Dict[str, Any]]:
    """Create mock node data for testing."""
    return [
        {
            'id': '1',
            'title': 'Test Paper 1',
            'citation_count': 100,
            'embedding_vector': np.array([0.1, 0.2, 0.3]),
            'primary_cluster': 0,
            'topic_cluster': 0
        },
        {
            'id': '2',
            'title': 'Test Paper 2',
            'citation_count': 200,
            'embedding_vector': np.array([0.2, 0.3, 0.4]),
            'primary_cluster': 0,
            'topic_cluster': 1
        },
        {
            'id': '3',
            'title': 'Test Paper 3',
            'citation_count': 150,
            'embedding_vector': np.array([0.3, 0.4, 0.5]),
            'primary_cluster': 1,
            'topic_cluster': 0
        }
    ]

@pytest.fixture
def sample_dataframe(mock_node_data) -> pd.DataFrame:
    """Create a sample DataFrame from mock node data."""
    return pd.DataFrame(mock_node_data)

@pytest.fixture
def isolated_node_graph() -> nx.Graph:
    """Create a graph with an isolated node for edge case testing."""
    G = nx.Graph()
    G.add_node(1, title="Isolated Node", citation_count=0, 
               embedding_vector=np.array([0.1]), primary_cluster=0, topic_cluster=0)
    G.add_node(2, title="Connected Node", citation_count=10, 
               embedding_vector=np.array([0.2]), primary_cluster=1, topic_cluster=1)
    G.add_edge(2, 2)  # Self-loop only
    return G

@pytest.fixture
def single_node_cluster_graph() -> nx.Graph:
    """Create a graph where one cluster has only a single node."""
    G = nx.Graph()
    G.add_node(1, title="Node 1", citation_count=10, 
               embedding_vector=np.array([0.1]), primary_cluster=0, topic_cluster=0)
    G.add_node(2, title="Node 2", citation_count=20, 
               embedding_vector=np.array([0.2]), primary_cluster=0, topic_cluster=0)
    G.add_node(3, title="Node 3", citation_count=30, 
               embedding_vector=np.array([0.3]), primary_cluster=1, topic_cluster=1)
    G.add_edge(1, 2)
    # Node 3 is in its own cluster with no edges to other clusters
    return G

@pytest.fixture
def complete_graph() -> nx.Graph:
    """Create a complete graph for testing bridging coefficient of 0."""
    G = nx.complete_graph(5)
    for i in range(5):
        G.nodes[i]['title'] = f"Node {i}"
        G.nodes[i]['citation_count'] = i * 10
        G.nodes[i]['embedding_vector'] = np.array([i * 0.1])
        G.nodes[i]['primary_cluster'] = 0
        G.nodes[i]['topic_cluster'] = 0
    return G

def configure_paths(base_dir: Path) -> None:
    """Configure paths for the test environment."""
    data_dir = base_dir / 'data'
    artifacts_dir = base_dir / 'artifacts'
    
    (data_dir / 'raw').mkdir(parents=True, exist_ok=True)
    (data_dir / 'processed').mkdir(parents=True, exist_ok=True)
    (artifacts_dir / 'results').mkdir(parents=True, exist_ok=True)
    (artifacts_dir / 'plots').mkdir(parents=True, exist_ok=True)
    (data_dir / 'logs').mkdir(parents=True, exist_ok=True)