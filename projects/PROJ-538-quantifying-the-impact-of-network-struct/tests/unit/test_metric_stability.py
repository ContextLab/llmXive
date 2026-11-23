"""
Test suite for T050: Metric Stability Test.

Verifies that MetricCalculator (T020) produces identical results for the same
graph input across multiple runs, ensuring no floating-point non-determinism
affects the correlation analysis.
"""
import pytest
import networkx as nx
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.metrics import MetricCalculator
from code.models import DefectGraph
from code.config import Config


class TestMetricStability:
    """Tests for deterministic behavior of MetricCalculator."""

    @pytest.fixture
    def sample_defect_graph(self):
        """Create a reproducible sample DefectGraph for testing."""
        # Create a deterministic graph structure
        G = nx.Graph()
        
        # Add nodes with specific attributes
        nodes = [
            (0, {"species": "Cu", "pos": [0.0, 0.0, 0.0]}),
            (1, {"species": "Ni", "pos": [1.0, 0.0, 0.0]}),
            (2, {"species": "Cu", "pos": [0.5, 0.866, 0.0]}),
            (3, {"species": "Au", "pos": [2.0, 0.0, 0.0]}),
            (4, {"species": "Ag", "pos": [1.5, 0.866, 0.0]}),
            (5, {"species": "Cu", "pos": [1.0, 1.732, 0.0]}),
        ]
        G.add_nodes_from(nodes)
        
        # Add edges (mismatched species only)
        edges = [
            (0, 1),  # Cu-Ni
            (1, 3),  # Ni-Au
            (2, 5),  # Cu-Cu (should be ignored in defect graph, but included here for test)
            (3, 4),  # Au-Ag
            (4, 5),  # Ag-Cu
        ]
        G.add_edges_from(edges)
        
        # Create DefectGraph model instance
        return DefectGraph(
            graph_data=G,
            snapshot_id="test_snapshot_stability",
            species_count={"Cu": 3, "Ni": 1, "Au": 1, "Ag": 1},
            total_atoms=6
        )

    @pytest.fixture
    def calculator(self):
        """Provide a MetricCalculator instance."""
        return MetricCalculator()

    def test_clustering_coefficient_determinism(self, sample_defect_graph, calculator):
        """Verify clustering coefficient is identical across multiple runs."""
        results = []
        num_runs = 10
        
        for _ in range(num_runs):
            result = calculator.calculate_clustering_coefficient(sample_defect_graph)
            results.append(result)
        
        # All results must be exactly equal
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result == first_result, (
                f"Clustering coefficient differs on run {i}: "
                f"{result} != {first_result}"
            )

    def test_mean_degree_determinism(self, sample_defect_graph, calculator):
        """Verify mean degree is identical across multiple runs."""
        results = []
        num_runs = 10
        
        for _ in range(num_runs):
            result = calculator.calculate_mean_degree(sample_defect_graph)
            results.append(result)
        
        # All results must be exactly equal
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result == first_result, (
                f"Mean degree differs on run {i}: "
                f"{result} != {first_result}"
            )

    def test_degree_distribution_moments_determinism(self, sample_defect_graph, calculator):
        """Verify degree distribution moments are identical across multiple runs."""
        results = []
        num_runs = 10
        
        for _ in range(num_runs):
            result = calculator.calculate_degree_distribution_moments(sample_defect_graph)
            results.append(result)
        
        # All results must be exactly equal
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result == first_result, (
                f"Degree distribution moments differ on run {i}: "
                f"{result} != {first_result}"
            )

    def test_percolation_threshold_determinism(self, sample_defect_graph, calculator):
        """Verify percolation threshold is identical across multiple runs."""
        results = []
        num_runs = 10
        
        for _ in range(num_runs):
            result = calculator.calculate_percolation_threshold(sample_defect_graph)
            results.append(result)
        
        # All results must be exactly equal (handling NaN case)
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            if np.isnan(first_result):
                assert np.isnan(result), (
                    f"Percolation threshold NaN mismatch on run {i}: "
                    f"{result} != {first_result}"
                )
            else:
                assert result == first_result, (
                    f"Percolation threshold differs on run {i}: "
                    f"{result} != {first_result}"
                )

    def test_full_metric_extraction_determinism(self, sample_defect_graph, calculator):
        """Verify full metric extraction produces identical results across runs."""
        results = []
        num_runs = 10
        
        for _ in range(num_runs):
            result = calculator.extract_all_metrics(sample_defect_graph)
            results.append(result)
        
        # All results must be exactly equal
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result == first_result, (
                f"Full metric extraction differs on run {i}: "
                f"{result} != {first_result}"
            )

    def test_large_graph_stability(self):
        """Test stability on a larger, more complex graph."""
        # Create a larger deterministic graph
        G = nx.erdos_renyi_graph(n=100, p=0.1, seed=42)
        
        # Add species attributes deterministically
        species_list = ["Cu", "Ni", "Au", "Ag"]
        for node in G.nodes():
            G.nodes[node]["species"] = species_list[node % 4]
            G.nodes[node]["pos"] = [
                (node * 1.234) % 10,
                (node * 5.678) % 10,
                (node * 9.012) % 10
            ]
        
        # Filter edges to only mismatched species
        edges_to_remove = []
        for u, v in G.edges():
            if G.nodes[u]["species"] == G.nodes[v]["species"]:
                edges_to_remove.append((u, v))
        G.remove_edges_from(edges_to_remove)
        
        defect_graph = DefectGraph(
            graph_data=G,
            snapshot_id="large_stability_test",
            species_count={s: sum(1 for n in G.nodes() if G.nodes[n]["species"] == s) 
                           for s in species_list},
            total_atoms=100
        )
        
        calculator = MetricCalculator()
        results = []
        num_runs = 5  # Fewer runs for larger graph
        
        for _ in range(num_runs):
            result = calculator.extract_all_metrics(defect_graph)
            results.append(result)
        
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result == first_result, (
                f"Large graph metric extraction differs on run {i}: "
                f"{result} != {first_result}"
            )

    def test_disconnected_graph_stability(self):
        """Test stability on a disconnected graph."""
        G = nx.Graph()
        G.add_nodes_from([
            (0, {"species": "Cu", "pos": [0, 0, 0]}),
            (1, {"species": "Ni", "pos": [1, 0, 0]}),
            (2, {"species": "Au", "pos": [10, 10, 10]}),  # Isolated node
            (3, {"species": "Ag", "pos": [11, 10, 10]}),  # Isolated node
        ])
        G.add_edges_from([(0, 1)])  # Only one edge, others disconnected
        
        defect_graph = DefectGraph(
            graph_data=G,
            snapshot_id="disconnected_stability_test",
            species_count={"Cu": 1, "Ni": 1, "Au": 1, "Ag": 1},
            total_atoms=4
        )
        
        calculator = MetricCalculator()
        results = []
        num_runs = 5
        
        for _ in range(num_runs):
            result = calculator.extract_all_metrics(defect_graph)
            results.append(result)
        
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result == first_result, (
                f"Disconnected graph metric extraction differs on run {i}: "
                f"{result} != {first_result}"
            )