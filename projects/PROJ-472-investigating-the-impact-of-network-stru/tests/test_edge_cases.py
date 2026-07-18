"""
Test suite for edge cases: disconnected graphs, sparse connectivity, and power-law convergence failures.
This test suite verifies that metrics.py, quality_control.py, and fitting.py handle these cases robustly.
"""
import os
import sys
import json
import tempfile
import logging
from pathlib import Path
import numpy as np
import networkx as nx
import pytest

# Add the project root to the path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from data.quality_control import check_graph_connectivity, calculate_pipeline_completeness
from analysis.metrics import compute_degree_centrality, compute_clustering_coefficient, run_metrics_pipeline
from analysis.fitting import fit_power_law_model, run_fitting_for_subject
from utils.logger import setup_logger

# Setup logger for tests
logger = setup_logger("test_edge_cases", level=logging.DEBUG)


class TestDisconnectedGraphs:
    """Tests for handling disconnected structural graphs in metrics and QC."""

    def test_check_graph_connectivity_disconnected_graph(self):
        """Verify that a disconnected graph is correctly identified as disconnected."""
        # Create a disconnected graph (two separate components)
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4, 5])
        G.add_edges_from([(1, 2), (2, 3)])  # Component 1
        G.add_edges_from([(4, 5)])          # Component 2

        is_connected, num_components = check_graph_connectivity(G)

        assert is_connected is False, "Graph should be identified as disconnected"
        assert num_components == 2, "Graph should have exactly 2 components"

    def test_check_graph_connectivity_single_node(self):
        """Verify that a single-node graph (no edges) is handled correctly."""
        G = nx.Graph()
        G.add_node(1)

        is_connected, num_components = check_graph_connectivity(G)

        # A single node with no edges is technically connected (1 component),
        # but for structural connectomes, this usually implies a failure or exclusion.
        # The function should return True for connectivity (1 component) but the
        # calling logic (QC) might exclude it based on edge count.
        assert is_connected is True
        assert num_components == 1

    def test_check_graph_connectivity_empty_graph(self):
        """Verify that an empty graph (no nodes) is handled correctly."""
        G = nx.Graph()

        is_connected, num_components = check_graph_connectivity(G)

        # Empty graph: 0 components, not connected
        assert is_connected is False
        assert num_components == 0

    def test_check_graph_connectivity_connected_graph(self):
        """Verify that a fully connected graph is identified as connected."""
        G = nx.complete_graph(5)

        is_connected, num_components = check_graph_connectivity(G)

        assert is_connected is True
        assert num_components == 1

    def test_compute_metrics_on_disconnected_graph(self):
        """Verify that metrics are computed correctly (or return NaN/0) for disconnected graphs."""
        # Create a disconnected graph
        G = nx.Graph()
        G.add_nodes_from([1, 2, 3, 4])
        G.add_edges_from([(1, 2), (3, 4)])

        # Degree centrality should still be computable
        degree_centrality = compute_degree_centrality(G)
        assert isinstance(degree_centrality, dict)
        assert len(degree_centrality) == 4
        # Nodes 1 and 2 should have degree 1, nodes 3 and 4 should have degree 1
        # (in a 4-node graph, max degree is 3, so centrality is 1/3)
        for node in G.nodes():
            assert degree_centrality[node] >= 0

        # Clustering coefficient might be 0 for disconnected nodes
        clustering = compute_clustering_coefficient(G)
        assert isinstance(clustering, dict)
        assert len(clustering) == 4

    def test_run_metrics_pipeline_with_disconnected_graph(self):
        """Verify that the metrics pipeline handles disconnected graphs without crashing."""
        # Create a temporary directory for test output
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create a mock connectome file for a disconnected graph
            # We simulate the output of preprocess_dMRI by creating a simple adjacency matrix
            # that results in a disconnected graph.
            # Graph: 0-1, 2-3 (two separate edges)
            adj_matrix = np.array([
                [0, 1, 0, 0],
                [1, 0, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0]
            ], dtype=float)

            # Save the matrix in a format that run_metrics_pipeline expects
            # Assuming the pipeline looks for .npy or .csv files in a specific structure
            # We'll create a mock subject directory structure
            subject_id = "sub-test001"
            connectome_dir = tmp_path / "connectomes" / subject_id
            connectome_dir.mkdir(parents=True)

            matrix_file = connectome_dir / "connectome_matrix.npy"
            np.save(matrix_file, adj_matrix)

            # Run the metrics pipeline on this subject
            # We need to mock the config or pass the path directly if the function allows
            # For this test, we'll call run_metrics_pipeline with the tmp_path
            # Note: run_metrics_pipeline expects a specific directory structure, so we adapt
            try:
                results = run_metrics_pipeline(str(tmp_path))
                # If it doesn't crash, it's a success. We check that results exist
                assert results is not None
                assert isinstance(results, dict)
                # Check that the subject is in the results
                assert subject_id in results
            except Exception as e:
                # If the pipeline crashes, it's a failure
                pytest.fail(f"run_metrics_pipeline crashed on disconnected graph: {e}")


class TestSparseConnectivity:
    """Tests for handling sparse connectivity (very low edge density)."""

    def test_check_graph_connectivity_very_sparse(self):
        """Verify that a very sparse graph (few edges) is handled correctly."""
        # Create a sparse graph: 10 nodes, only 2 edges
        G = nx.Graph()
        G.add_nodes_from(range(10))
        G.add_edges_from([(0, 1), (2, 3)])

        is_connected, num_components = check_graph_connectivity(G)

        assert is_connected is False
        assert num_components == 8  # 2 edges connect 4 nodes, leaving 6 isolated + 1 component per edge = 2 + 6 = 8

    def test_compute_metrics_on_sparse_graph(self):
        """Verify that metrics are computed correctly for sparse graphs."""
        G = nx.Graph()
        G.add_nodes_from(range(10))
        G.add_edges_from([(0, 1), (2, 3), (4, 5)])

        degree_centrality = compute_degree_centrality(G)
        clustering = compute_clustering_coefficient(G)

        # Ensure no NaN or inf values
        for node, val in degree_centrality.items():
            assert np.isfinite(val), f"Degree centrality for node {node} is not finite"

        for node, val in clustering.items():
            assert np.isfinite(val), f"Clustering coefficient for node {node} is not finite"


class TestPowerLawConvergence:
    """Tests for handling power-law fitting convergence failures."""

    def test_fit_power_law_model_convergence_failure(self):
        """Verify that fit_power_law_model handles convergence failures gracefully."""
        # Create data that is likely to cause convergence failure for power-law fitting
        # For example, a very small dataset or data that doesn't fit any distribution well
        # We'll use a tiny dataset of constant values
        data = np.array([1.0, 1.0, 1.0, 1.0, 1.0])

        try:
            result = fit_power_law_model(data)
            # The function should return a result object, possibly with a flag indicating failure
            # or it should raise a specific exception. We check that it doesn't crash with a generic error.
            # If it returns None or a special value for failure, that's acceptable.
            assert result is not None, "fit_power_law_model should return a result even on failure"
            # Check if the result has a 'success' or 'converged' attribute
            if hasattr(result, 'success'):
                # If it's not successful, that's okay for this test
                pass
        except Exception as e:
            # If it raises a specific exception (e.g., ConvergenceError), that's also acceptable
            # as long as it's not a generic crash
            assert "convergence" in str(e).lower() or "fit" in str(e).lower(), \
                f"Unexpected error type: {e}"

    def test_fit_power_law_model_nan_input(self):
        """Verify that fit_power_law_model handles NaN input gracefully."""
        data = np.array([1.0, np.nan, 3.0, 4.0, 5.0])

        try:
            result = fit_power_law_model(data)
            # Should handle NaNs (e.g., by filtering them out or returning a failure status)
            assert result is not None
        except Exception as e:
            # If it raises, it should be a clear error, not a crash
            assert "nan" in str(e).lower() or "invalid" in str(e).lower(), \
                f"Unexpected error type: {e}"

    def test_fit_power_law_model_small_sample(self):
        """Verify that fit_power_law_model handles very small samples gracefully."""
        data = np.array([1.0, 2.0])  # Only 2 data points

        try:
            result = fit_power_law_model(data)
            # Should handle small samples (e.g., by returning a failure status)
            assert result is not None
        except Exception as e:
            # If it raises, it should be a clear error
            assert "sample" in str(e).lower() or "too small" in str(e).lower() or "fit" in str(e).lower(), \
                f"Unexpected error type: {e}"

    def test_run_fitting_for_subject_with_convergence_failure(self):
        """Verify that run_fitting_for_subject handles convergence failures without crashing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create a mock avalanche events file with data that will cause convergence failure
            subject_id = "sub-test002"
            avalanches_dir = tmp_path / "avalanches" / subject_id
            avalanches_dir.mkdir(parents=True)

            # Create a CSV with constant avalanche sizes (will fail to fit a power law)
            events_file = avalanches_dir / "avalanche_events.csv"
            import pandas as pd
            df = pd.DataFrame({
                'size': [1.0, 1.0, 1.0, 1.0, 1.0],
                'duration': [1.0, 1.0, 1.0, 1.0, 1.0],
                'timestamp': [0.0, 1.0, 2.0, 3.0, 4.0],
                'participant_id': [subject_id] * 5
            })
            df.to_csv(events_file, index=False)

            # Run fitting for this subject
            try:
                result = run_fitting_for_subject(str(tmp_path), subject_id)
                # Should not crash
                assert result is not None
                # Check if the result indicates a failure
                if isinstance(result, dict):
                    assert 'success' in result or 'converged' in result or 'error' in result
            except Exception as e:
                # If it raises, it should be a clear error, not a crash
                pytest.fail(f"run_fitting_for_subject crashed on convergence failure: {e}")


class TestIntegrationEdgeCases:
    """Integration tests for edge cases across multiple modules."""

    def test_full_pipeline_with_disconnected_graph(self):
        """Test the full pipeline (QC -> Metrics) with a disconnected graph."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create a mock connectome matrix for a disconnected graph
            subject_id = "sub-test003"
            connectome_dir = tmp_path / "connectomes" / subject_id
            connectome_dir.mkdir(parents=True)

            # Disconnected graph: 0-1, 2-3
            adj_matrix = np.array([
                [0, 1, 0, 0],
                [1, 0, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 0]
            ], dtype=float)

            matrix_file = connectome_dir / "connectome_matrix.npy"
            np.save(matrix_file, adj_matrix)

            # Run QC
            qc_result = check_graph_connectivity(nx.from_numpy_array(adj_matrix))
            is_connected, num_components = qc_result

            assert is_connected is False, "Disconnected graph should be detected by QC"

            # Run metrics
            try:
                metrics = run_metrics_pipeline(str(tmp_path))
                assert metrics is not None
                assert subject_id in metrics
            except Exception as e:
                pytest.fail(f"Full pipeline crashed on disconnected graph: {e}")

    def test_full_pipeline_with_convergence_failure(self):
        """Test the full pipeline (Avalanches -> Fitting) with convergence failure data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            subject_id = "sub-test004"
            avalanches_dir = tmp_path / "avalanches" / subject_id
            avalanches_dir.mkdir(parents=True)

            # Create data that will cause convergence failure
            import pandas as pd
            events_file = avalanches_dir / "avalanche_events.csv"
            df = pd.DataFrame({
                'size': [1.0, 1.0, 1.0, 1.0, 1.0],
                'duration': [1.0, 1.0, 1.0, 1.0, 1.0],
                'timestamp': [0.0, 1.0, 2.0, 3.0, 4.0],
                'participant_id': [subject_id] * 5
            })
            df.to_csv(events_file, index=False)

            # Run fitting
            try:
                result = run_fitting_for_subject(str(tmp_path), subject_id)
                assert result is not None
                # Verify that the result indicates a failure or is handled gracefully
                if isinstance(result, dict):
                    assert 'success' in result or 'converged' in result or 'error' in result
            except Exception as e:
                pytest.fail(f"Full pipeline crashed on convergence failure: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])