import os
import tempfile
import pytest
import pandas as pd
import networkx as nx
from unittest.mock import patch, MagicMock

from src.services.save_graph import save_graph_to_parquet, main
from src.lib.config import get_config

@pytest.fixture
def sample_graph():
    """Create a simple graph for testing."""
    G = nx.Graph()
    G.add_node(1, title="Paper A", citation_count=10, primary_cluster=0, bridging_coefficient=0.5)
    G.add_node(2, title="Paper B", citation_count=20, primary_cluster=0, bridging_coefficient=0.3)
    G.add_node(3, title="Paper C", citation_count=30, primary_cluster=1, bridging_coefficient=0.8)
    G.add_edge(1, 2)
    G.add_edge(2, 3)
    return G

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_save_graph_creates_file(sample_graph, temp_output_dir):
    """Test that save_graph_to_parquet creates the output file."""
    output_path = os.path.join(temp_output_dir, "test_output.parquet")
    save_graph_to_parquet(sample_graph, output_path)
    
    assert os.path.exists(output_path), "Output file was not created."
    
    # Verify content
    df = pd.read_parquet(output_path)
    assert len(df) == 3, "DataFrame does not have the expected number of rows."
    assert 'id' in df.columns, "Missing 'id' column."
    assert 'bridging_coefficient' in df.columns, "Missing 'bridging_coefficient' column."
    assert df['id'].tolist() == [1, 2, 3], "Node IDs do not match."

def test_save_graph_handles_empty_graph(temp_output_dir):
    """Test that save_graph_to_parquet handles an empty graph."""
    G = nx.Graph()
    output_path = os.path.join(temp_output_dir, "empty_output.parquet")
    
    save_graph_to_parquet(G, output_path)
    
    assert os.path.exists(output_path), "Output file was not created for empty graph."
    df = pd.read_parquet(output_path)
    assert len(df) == 0, "DataFrame should be empty."

def test_main_integration_flow(temp_output_dir, sample_graph):
    """Test the main function integration flow with mocked dependencies."""
    output_filename = "subgraph_with_clusters.parquet"
    output_path = os.path.join(temp_output_dir, output_filename)
    
    # Mock get_config to return a path in temp_output_dir
    with patch('src.services.save_graph.get_config') as mock_cfg, \
         patch('src.services.save_graph.fetch_and_build_subgraph') as mock_fetch, \
         patch('src.services.save_graph.louvain_cluster') as mock_louvain, \
         patch('src.services.save_graph.calc_bridging') as mock_bridging:
         
         # Setup mocks
         mock_cfg.return_value = {
             'paths': {
                 'processed_data': type('obj', (object,), {'__truediv__': lambda self, x: os.path.join(temp_output_dir, x)})()
             },
             'sampling': {'target_size': 100}
         }
         mock_fetch.return_value = sample_graph
         mock_louvain.return_value = {1: 0, 2: 0, 3: 1}
         mock_bridging.return_value = {1: 0.5, 2: 0.3, 3: 0.8}
         
         # Run main
         main()
         
         # Verify output
         assert os.path.exists(output_path), f"Output file {output_path} was not created."
         df = pd.read_parquet(output_path)
         assert len(df) == 3
         assert 'bridging_coefficient' in df.columns
         assert 'primary_cluster' in df.columns
         assert 'citation_count' in df.columns
         assert 'title' in df.columns