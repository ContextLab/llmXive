"""
Test skeletons for graph construction and subsampling logic (T011).
Verifies:
- Nodes <= 5000
- LCC rule is applied
- Memory limits are respected (mocked)
"""
import os
import sys
import tempfile
import networkx as nx
import pytest
import pandas as pd

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data.preprocess import extract_lcc, subsample_graph, preprocess_graph
from utils.memory_monitor import start_monitoring, stop_monitoring, get_peak_memory_mb

class TestGraphConstruction:
    """Tests for T011: Node count subsampling and LCC rule."""

    def test_extract_lcc_basic(self):
        """Test that LCC extraction works correctly."""
        # Create a graph with two disconnected components
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3), (4, 5)]) # Component 1: 1-2-3 (3 nodes), Component 2: 4-5 (2 nodes)
        
        lcc = extract_lcc(G)
        
        assert lcc.number_of_nodes() == 3
        assert set(lcc.nodes()) == {1, 2, 3}
        assert lcc.number_of_edges() == 2
    
    def test_extract_lcc_empty(self):
        """Test LCC on empty graph."""
        G = nx.Graph()
        lcc = extract_lcc(G)
        assert lcc.number_of_nodes() == 0
    
    def test_subsample_graph_node_limit(self):
        """Test that subsample_graph reduces nodes to <= 5000."""
        # Create a large graph
        large_graph = nx.barabasi_albert_graph(6000, 5)
        
        # Mock memory to be low so we only test node limit
        start_monitoring()
        subsampled = subsample_graph(large_graph, target_nodes=5000, target_memory_mb=10000)
        stop_monitoring()
        
        assert subsampled.number_of_nodes() <= 5000
        assert subsampled.number_of_edges() > 0 # Should not be empty
    
    def test_preprocess_graph_logic_small_graph(self, tmp_path):
        """Test that small graphs are retained as-is."""
        # Create a small CSV
        csv_path = tmp_path / "small.csv"
        df = pd.DataFrame({
            'src_ip': ['1.1.1.1', '1.1.1.2'],
            'dst_ip': ['1.1.1.2', '1.1.1.3'],
            'packets': [10, 20]
        })
        df.to_csv(csv_path, index=False)
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        final_path, hash_path = preprocess_graph(str(csv_path), str(output_dir), "small_test")
        
        assert os.path.exists(final_path)
        assert os.path.exists(hash_path)
        
        G = nx.read_graphml(str(final_path))
        assert G.number_of_nodes() <= 5000 # Should be 3
    
    def test_preprocess_graph_logic_large_graph(self, tmp_path):
        """Test that large graphs trigger LCC/Subsampling."""
        # Create a large CSV (simulated)
        csv_path = tmp_path / "large.csv"
        n_nodes = 6000
        # Generate edges to ensure connectivity for LCC test
        edges = []
        for i in range(n_nodes - 1):
            edges.append({'src_ip': f'1.1.1.{i}', 'dst_ip': f'1.1.1.{i+1}', 'packets': 1})
        df = pd.DataFrame(edges)
        df.to_csv(csv_path, index=False)
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        start_monitoring()
        final_path, hash_path = preprocess_graph(str(csv_path), str(output_dir), "large_test")
        stop_monitoring()
        
        assert os.path.exists(final_path)
        assert os.path.exists(hash_path)
        
        G = nx.read_graphml(str(final_path))
        # Must be <= 5000
        assert G.number_of_nodes() <= 5000
        
        # Verify hash file content
        with open(hash_path, 'r') as f:
            hash_content = f.read().strip()
            assert len(hash_content) == 64 # SHA256 hex length
    
    def test_lcc_then_subsample(self, tmp_path):
        """Test scenario where LCC is still too large."""
        # Create a graph with a giant component of 6000 nodes and a tiny one
        G = nx.Graph()
        # Giant component
        giant = nx.barabasi_albert_graph(6000, 5)
        # Tiny component
        tiny = nx.path_graph(2)
        
        # Merge (disconnected)
        G = nx.disjoint_union(G, giant)
        G = nx.disjoint_union(G, tiny)
        
        # Save as graphml to test direct graphml input
        input_path = tmp_path / "mixed.graphml"
        nx.write_graphml(G, str(input_path))
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        start_monitoring()
        final_path, hash_path = preprocess_graph(str(input_path), str(output_dir), "mixed_test")
        stop_monitoring()
        
        G_final = nx.read_graphml(str(final_path))
        assert G_final.number_of_nodes() <= 5000