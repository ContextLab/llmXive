import os
import tempfile
import pytest
import pandas as pd
import networkx as nx
from unittest.mock import patch, MagicMock
from src.services.save_graph import save_graph_to_parquet

@pytest.fixture
def sample_graph():
    G = nx.Graph()
    G.add_node("1", title="A", citation_count=10, primary_cluster=1, topic_cluster=2)
    G.add_node("2", title="B", citation_count=20, primary_cluster=1, topic_cluster=2)
    G.add_edge("1", "2")
    return G

def test_save_graph_creates_file(sample_graph):
    """
    Test that save_graph_to_parquet creates the output file.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test_graph.parquet")
        save_graph_to_parquet(sample_graph, path)
        
        assert os.path.exists(path)
        
        # Verify content
        df = pd.read_parquet(path)
        assert 'id' in df.columns
        assert 'title' in df.columns
        assert len(df) == 2

def test_save_graph_handles_empty_graph():
    """
    Test saving an empty graph.
    """
    G = nx.Graph()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "empty_graph.parquet")
        save_graph_to_parquet(G, path)
        
        assert os.path.exists(path)
        df = pd.read_parquet(path)
        assert len(df) == 0
