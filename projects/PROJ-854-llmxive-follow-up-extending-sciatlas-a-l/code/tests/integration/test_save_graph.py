import os
import tempfile
import pytest
import pandas as pd
import networkx as nx
from unittest.mock import patch, MagicMock

from src.services.save_graph import save_graph_to_parquet
from src.lib import config

@pytest.fixture
def sample_graph():
    G = nx.Graph()
    G.add_node(1, title="Test Paper 1", citation_count=10)
    G.add_node(2, title="Test Paper 2", citation_count=20)
    G.add_edge(1, 2)
    return G

def test_save_graph_creates_file(sample_graph):
    """
    Test that save_graph_to_parquet creates the file and writes valid data.
    """
    clusters = {1: 0, 2: 0}
    bridging_coeffs = {1: 0.5, 2: 0.5}

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_output.parquet")

        save_graph_to_parquet(
            sample_graph,
            clusters,
            bridging_coeffs,
            output_path
        )

        assert os.path.exists(output_path), "Output file was not created"

        df = pd.read_parquet(output_path)
        assert len(df) == 2, "Incorrect number of rows"
        assert 'id' in df.columns, "Missing 'id' column"
        assert 'primary_cluster' in df.columns, "Missing 'primary_cluster' column"
        assert 'bridging_coefficient' in df.columns, "Missing 'bridging_coefficient' column"
        
        # Verify specific values
        assert df.loc[df['id'] == 1, 'primary_cluster'].iloc[0] == 0
        assert df.loc[df['id'] == 1, 'bridging_coefficient'].iloc[0] == 0.5

def test_save_graph_handles_empty_graph():
    """
    Test behavior when graph has no nodes.
    """
    G = nx.Graph()
    clusters = {}
    bridging_coeffs = {}

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "empty_output.parquet")
        
        # Should not raise, just save empty dataframe
        save_graph_to_parquet(G, clusters, bridging_coeffs, output_path)
        
        assert os.path.exists(output_path)
        df = pd.read_parquet(output_path)
        assert len(df) == 0
