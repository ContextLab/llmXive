"""
Unit tests for edge cases in the analysis pipeline.
Specifically targets:
1. Power-law convergence failure handling (fitting.py)
2. Disconnected graph handling (metrics.py)
"""
import os
import sys
import tempfile
import json
import numpy as np
import pandas as pd
import networkx as nx
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.fitting import fit_power_law_model, load_avalanche_sizes_from_store
from analysis.metrics import compute_degree_centrality, compute_clustering_coefficient, compute_rich_club_coefficient
from data.models import Participant, StructuralConnectome, AvalancheRecord
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TestPowerLawConvergenceFailure:
    """Tests for handling power-law fitting convergence failures."""

    def test_fit_power_law_with_empty_sizes(self):
        """Test that empty avalanche sizes raise a clear error or return None."""
        empty_sizes = np.array([])
        result = fit_power_law_model(empty_sizes)
        # Expecting None or a specific failure indicator as per T033
        assert result is None or result.get("status") == "failed"

    def test_fit_power_law_with_single_value(self):
        """Test fitting with a single data point (convergence likely to fail)."""
        single_size = np.array([5.0])
        result = fit_power_law_model(single_size)
        # Should not crash, but indicate failure
        assert result is None or result.get("status") == "failed"

    def test_fit_power_law_with_constant_values(self):
        """Test fitting with constant values (no variance, convergence failure)."""
        constant_sizes = np.array([3.0, 3.0, 3.0, 3.0])
        result = fit_power_law_model(constant_sizes)
        assert result is None or result.get("status") == "failed"

    def test_fit_power_law_with_valid_data(self):
        """Test that valid data returns a successful fit."""
        # Generate synthetic power-law distributed data for testing
        # Using a simple Pareto-like distribution
        valid_sizes = np.random.pareto(a=2.0, size=1000) + 1  # Ensure min >= 1
        result = fit_power_law_model(valid_sizes)
        # Should succeed
        assert result is not None and result.get("status") != "failed"
        assert "alpha" in result
        assert "xmin" in result

    def test_fit_power_law_handles_nan(self):
        """Test fitting with NaN values."""
        sizes_with_nan = np.array([1.0, 2.0, np.nan, 4.0])
        result = fit_power_law_model(sizes_with_nan)
        # Should handle gracefully, likely failing or cleaning data
        assert result is not None  # Should not crash


class TestDisconnectedGraphs:
    """Tests for handling disconnected structural connectome graphs."""

    def test_compute_degree_on_disconnected_graph(self):
        """Test degree centrality calculation on a disconnected graph."""
        # Create a disconnected graph: two separate components
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3)])  # Component 1
        G.add_edges_from([(4, 5)])          # Component 2

        degree = compute_degree_centrality(G)
        # Should return a dictionary with degrees for all nodes
        assert isinstance(degree, dict)
        assert len(degree) == 5
        # Nodes 1, 2, 3, 4, 5 should have non-negative degrees
        for node, deg in degree.items():
            assert deg >= 0

    def test_compute_clustering_on_disconnected_graph(self):
        """Test clustering coefficient on a disconnected graph."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3)])
        G.add_edges_from([(4, 5)])

        clustering = compute_clustering_coefficient(G)
        assert isinstance(clustering, dict)
        assert len(clustering) == 5

    def test_compute_rich_club_on_disconnected_graph(self):
        """Test rich-club coefficient on a disconnected graph."""
        G = nx.Graph()
        G.add_edges_from([(1, 2), (2, 3)])
        G.add_edges_from([(4, 5)])

        rich_club = compute_rich_club_coefficient(G)
        # Should return a dictionary or array, not crash
        assert rich_club is not None

    def test_compute_metrics_on_single_node_graph(self):
        """Test metrics on a graph with a single isolated node."""
        G = nx.Graph()
        G.add_node(1)

        degree = compute_degree_centrality(G)
        assert degree[1] == 0.0

        clustering = compute_clustering_coefficient(G)
        # Clustering for isolated node is typically 0 or NaN depending on definition
        assert clustering[1] == 0.0 or np.isnan(clustering[1])

    def test_compute_metrics_on_empty_graph(self):
        """Test metrics on a graph with no nodes."""
        G = nx.Graph()

        degree = compute_degree_centrality(G)
        assert degree == {}

        clustering = compute_clustering_coefficient(G)
        assert clustering == {}

    def test_compute_metrics_on_complete_graph(self):
        """Test metrics on a complete graph (all nodes connected)."""
        G = nx.complete_graph(5)

        degree = compute_degree_centrality(G)
        # In a complete graph of 5 nodes, degree centrality should be (5-1)/(5-1) = 1.0
        for node, deg in degree.items():
            assert np.isclose(deg, 1.0)

        clustering = compute_clustering_coefficient(G)
        # In a complete graph, clustering coefficient is 1.0
        for node, coef in clustering.items():
            assert np.isclose(coef, 1.0)


class TestIntegrationEdgeCases:
    """Integration tests combining edge cases with pipeline functions."""

    def test_run_fitting_pipeline_with_mixed_data(self):
        """Test fitting pipeline with a mix of valid and invalid subject data."""
        # Create a temporary store directory
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "avalanche_store"
            store_dir.mkdir()

            # Create valid data for one subject
            valid_sizes = np.random.pareto(a=2.0, size=500) + 1
            valid_df = pd.DataFrame({"size": valid_sizes, "subject_id": "sub_001"})
            valid_df.to_csv(store_dir / "sub_001_avalanches.csv", index=False)

            # Create invalid data (empty) for another subject
            invalid_df = pd.DataFrame(columns=["size", "subject_id"])
            invalid_df.to_csv(store_dir / "sub_002_avalanches.csv", index=False)

            # Run pipeline
            results = load_avalanche_sizes_from_store(store_dir)
            assert len(results) == 2
            assert "sub_001" in results
            assert "sub_002" in results

    def test_run_metrics_pipeline_with_disconnected_subjects(self):
        """Test metrics pipeline with subjects having disconnected connectomes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_dir = Path(tmpdir) / "connectome_store"
            store_dir.mkdir()

            # Create a connected graph for sub_001
            G1 = nx.erdos_renyi_graph(10, 0.3, seed=42)
            while not nx.is_connected(G1):
                G1 = nx.erdos_renyi_graph(10, 0.3, seed=42)
            nx.write_edgelist(G1, str(store_dir / "sub_001_connectome.edgelist"))

            # Create a disconnected graph for sub_002
            G2 = nx.Graph()
            G2.add_edges_from([(1, 2), (2, 3)])
            G2.add_edges_from([(4, 5)])
            nx.write_edgelist(G2, str(store_dir / "sub_002_connectome.edgelist"))

            # Run pipeline
            metrics = {}
            for subject_file in store_dir.glob("*.edgelist"):
                subject_id = subject_file.stem.replace("_connectome", "")
                G = nx.read_edgelist(subject_file)
                metrics[subject_id] = {
                    "degree": compute_degree_centrality(G),
                    "clustering": compute_clustering_coefficient(G),
                    "rich_club": compute_rich_club_coefficient(G)
                }

            assert len(metrics) == 2
            assert "sub_001" in metrics
            assert "sub_002" in metrics
            # Both should have computed metrics without crashing
            assert metrics["sub_001"]["degree"] is not None
            assert metrics["sub_002"]["degree"] is not None