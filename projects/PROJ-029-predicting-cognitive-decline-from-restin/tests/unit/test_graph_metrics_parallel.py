"""
Unit tests for T035: Parallel Graph Metrics Computation
"""
import pytest
import numpy as np
import networkx as nx
from pathlib import Path
import tempfile
import json

# Import functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from code.utils.graph import create_graph_from_adjacency, calculate_global_efficiency
from code.utils.io import save_csv, load_csv
from code.utils.logger import setup_logger
from code import config

# Setup logger for tests
logger = setup_logger("test_graph_metrics", level="DEBUG")

class TestGraphMetricsParallel:
    """Tests for parallel graph metrics computation."""

    def test_create_graph_from_adjacency(self):
        """Test graph creation from adjacency matrix."""
        # Create a simple 5x5 adjacency matrix
        adj_matrix = np.array([
            [0, 1, 1, 0, 0],
            [1, 0, 1, 1, 0],
            [1, 1, 0, 1, 1],
            [0, 1, 1, 0, 1],
            [0, 0, 1, 1, 0]
        ], dtype=float)

        G = create_graph_from_adjacency(adj_matrix)
        
        assert G.number_of_nodes() == 5
        assert G.number_of_edges() == 8  # Undirected, so 8 edges

    def test_calculate_global_efficiency(self):
        """Test global efficiency calculation."""
        # Create a complete graph (efficiency should be 1.0)
        G = nx.complete_graph(5)
        efficiency = calculate_global_efficiency(G)
        
        assert efficiency == 1.0

    def test_process_single_subject_matrix(self):
        """Test processing a single subject's matrix."""
        from code import process_single_subject_matrix
        
        # Create a temporary directory with a sample connectivity matrix
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            conn_dir = data_dir / "connectivity"
            conn_dir.mkdir()
            
            # Create a sample 90x90 connectivity matrix (AAL atlas size)
            np.random.seed(42)
            matrix = np.random.rand(90, 90)
            matrix = (matrix + matrix.T) / 2  # Symmetrize
            np.fill_diagonal(matrix, 0)  # No self-loops
            
            # Save matrix
            matrix_path = conn_dir / "test_subj_connectivity.npy"
            np.save(matrix_path, matrix)
            
            # Process
            result = process_single_subject_matrix("test_subj", data_dir)
            
            assert result is not None
            assert result["subject_id"] == "test_subj"
            assert "degree_centrality" in result
            assert "global_efficiency" in result
            assert "clustering_coefficient" in result
            assert "average_path_length" in result

    def test_compute_metrics_parallel(self):
        """Test parallel computation of metrics."""
        from code import compute_metrics_parallel
        
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir)
            conn_dir = data_dir / "connectivity"
            conn_dir.mkdir()
            
            # Create sample matrices for 3 subjects
            subject_ids = ["sub1", "sub2", "sub3"]
            for subj in subject_ids:
                matrix = np.random.rand(90, 90)
                matrix = (matrix + matrix.T) / 2
                np.fill_diagonal(matrix, 0)
                matrix_path = conn_dir / f"{subj}_connectivity.npy"
                np.save(matrix_path, matrix)
            
            # Compute metrics in parallel
            results = compute_metrics_parallel(subject_ids, data_dir, n_jobs=2)
            
            assert len(results) == 3
            for r in results:
                assert r is not None
                assert "subject_id" in r
                assert "degree_centrality" in r

    def test_write_outputs(self):
        """Test writing metrics to CSV."""
        from code import write_outputs
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_metrics.csv"
            
            metrics = [
                {"subject_id": "sub1", "degree_centrality": 0.5, "global_efficiency": 0.8},
                {"subject_id": "sub2", "degree_centrality": 0.6, "global_efficiency": 0.7}
            ]
            
            write_outputs(metrics, output_path)
            
            assert output_path.exists()
            df = load_csv(output_path)
            assert len(df) == 2
            assert "subject_id" in df.columns
            assert "degree_centrality" in df.columns
            assert "global_efficiency" in df.columns
