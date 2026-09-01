import os
import tempfile
import pytest
import pandas as pd
import networkx as nx
from unittest.mock import patch, MagicMock
from src.services.save_graph import save_graph_to_parquet, main
from src.lib.config import DATA_PATH

@pytest.fixture
def sample_graph():
    """Create a small sample graph with attributes."""
    G = nx.Graph()
    G.add_node(1, title="Paper A", citation_count=10, embedding_vector=[0.1, 0.2], primary_cluster=0, topic_cluster=1, bridging_coefficient=0.5)
    G.add_node(2, title="Paper B", citation_count=20, embedding_vector=[0.3, 0.4], primary_cluster=0, topic_cluster=1, bridging_coefficient=0.2)
    G.add_node(3, title="Paper C", citation_count=5, embedding_vector=[0.5, 0.6], primary_cluster=1, topic_cluster=2, bridging_coefficient=0.8)
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

    assert os.path.exists(output_path), "Output Parquet file was not created."

    # Verify content
    df = pd.read_parquet(output_path)
    assert len(df) == 3, "DataFrame should have 3 rows."
    assert 'id' in df.columns, "DataFrame should have 'id' column."
    assert 'bridging_coefficient' in df.columns, "DataFrame should have 'bridging_coefficient' column."
    assert df['bridging_coefficient'].iloc[0] == 0.5

def test_save_graph_handles_empty_graph(temp_output_dir):
    """Test that save_graph_to_parquet handles an empty graph."""
    G = nx.Graph()
    output_path = os.path.join(temp_output_dir, "empty_output.parquet")

    # Should not raise an error, just create an empty file
    save_graph_to_parquet(G, output_path)

    assert os.path.exists(output_path), "Output Parquet file was not created for empty graph."
    df = pd.read_parquet(output_path)
    assert len(df) == 0, "DataFrame should be empty."

@patch('src.services.save_graph.fetch_sample_ids')
@patch('src.services.save_graph.fetch_and_build_subgraph')
@patch('src.services.save_graph.louvain_cluster')
@patch('src.services.save_graph.calc_bridging')
@patch('src.services.save_graph.save_graph_to_parquet')
def test_main_integration_flow(mock_save, mock_calc, mock_louvain, mock_fetch_graph, mock_fetch_ids, temp_output_dir):
    """Test the main integration flow with mocked dependencies."""
    # Setup mocks
    mock_fetch_ids.return_value = [1, 2, 3]
    
    G = nx.Graph()
    G.add_node(1, title="Test")
    mock_fetch_graph.return_value = G
    
    mock_louvain_cluster.return_value = {1: 0}
    mock_calc.return_value = {1: 0.5}
    
    # Mock save_graph_to_parquet to just record the call
    def dummy_save(graph, path):
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        pd.DataFrame({'id': [1]}).to_parquet(path)
    
    mock_save.side_effect = dummy_save

    # Temporarily override DATA_PATH for the test
    original_data_path = DATA_PATH
    test_data_path = os.path.join(temp_output_dir, "test_data")
    
    # Patch the config import inside save_graph
    with patch('src.services.save_graph.DATA_PATH', test_data_path):
        main()

    # Verify calls
    mock_fetch_ids.assert_called_once_with(target_size=500)
    mock_fetch_graph.assert_called_once_with([1, 2, 3])
    mock_louvain_cluster.assert_called_once()
    mock_calc.assert_called_once()
    assert mock_save.called, "save_graph_to_parquet should have been called."

    # Check if file was created in the temp directory
    expected_path = os.path.join(test_data_path, "processed", "subgraph_with_clusters.parquet")
    # Since we mocked save_graph_to_parquet, we check if our dummy created it
    # In a real scenario, we would verify the actual file creation
    # Here we rely on the side_effect logic creating it if the path exists
    # For this test, we verify the logic flow
    assert mock_save.call_count == 1