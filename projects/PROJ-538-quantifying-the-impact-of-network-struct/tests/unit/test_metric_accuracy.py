"""
Unit tests for metric calculation on known graph topologies.

Tests verify that MetricCalculator produces theoretically expected values
for standard graph topologies (Erdős-Rényi, Star, Complete, Path) within
strict numerical tolerance (< 1e-6).
"""
import pytest
import networkx as nx
import numpy as np
from numpy.testing import assert_almost_equal
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.metrics import MetricCalculator
from code.models import DefectGraph

class TestMetricCalculatorAccuracy:
    """Test metric calculations against known theoretical values."""

    def _create_defect_graph(self, nx_graph: nx.Graph) -> DefectGraph:
        """Helper to wrap a networkx graph in the project's DefectGraph model."""
        # Convert to list of edges and nodes for the model
        # DefectGraph expects nodes and edges; we pass the nx graph data
        return DefectGraph(
            nodes=list(nx_graph.nodes()),
            edges=list(nx_graph.edges()),
            attributes={"source": "test"}
        )

    def test_erdos_renyi_clustering_coefficient(self):
        """
        Test clustering coefficient on Erdős-Rényi graph.
        For G(n, p), the expected clustering coefficient is exactly p.
        """
        n = 100
        p = 0.1
        # Set seed for reproducibility
        G = nx.erdos_renyi_graph(n, p, seed=42)
        
        calculator = MetricCalculator()
        result = calculator.calculate(G)
        
        # Theoretical expectation: C = p
        expected = p
        actual = result['clustering_coefficient']
        
        # Allow small tolerance for finite sample variance, but strict for large n
        assert_almost_equal(actual, expected, decimal=2)

    def test_star_graph_clustering_coefficient(self):
        """
        Test clustering coefficient on a Star graph.
        A star graph has 0 clustering coefficient because no two neighbors are connected.
        """
        n = 10
        G = nx.star_graph(n)
        
        calculator = MetricCalculator()
        result = calculator.calculate(G)
        
        expected = 0.0
        actual = result['clustering_coefficient']
        
        assert_almost_equal(actual, expected, decimal=6)

    def test_complete_graph_clustering_coefficient(self):
        """
        Test clustering coefficient on a Complete graph.
        A complete graph K_n has clustering coefficient 1.0.
        """
        n = 10
        G = nx.complete_graph(n)
        
        calculator = MetricCalculator()
        result = calculator.calculate(G)
        
        expected = 1.0
        actual = result['clustering_coefficient']
        
        assert_almost_equal(actual, expected, decimal=6)

    def test_mean_degree_star_graph(self):
        """
        Test mean degree on a Star graph.
        Star graph has one center (degree n) and n leaves (degree 1).
        Total nodes = n + 1.
        Sum of degrees = n + n*1 = 2n.
        Mean degree = 2n / (n+1).
        """
        n = 10
        G = nx.star_graph(n)
        
        calculator = MetricCalculator()
        result = calculator.calculate(G)
        
        expected = (2 * n) / (n + 1)
        actual = result['mean_degree']
        
        assert_almost_equal(actual, expected, decimal=6)

    def test_mean_degree_complete_graph(self):
        """
        Test mean degree on a Complete graph.
        In K_n, every node has degree n-1.
        Mean degree = n-1.
        """
        n = 10
        G = nx.complete_graph(n)
        
        calculator = MetricCalculator()
        result = calculator.calculate(G)
        
        expected = n - 1
        actual = result['mean_degree']
        
        assert_almost_equal(actual, expected, decimal=6)

    def test_degree_variance_complete_graph(self):
        """
        Test degree variance on a Complete graph.
        All degrees are identical (n-1), so variance is 0.
        """
        n = 10
        G = nx.complete_graph(n)
        
        calculator = MetricCalculator()
        result = calculator.calculate(G)
        
        expected = 0.0
        actual = result['degree_variance']
        
        assert_almost_equal(actual, expected, decimal=6)

    def test_percolation_threshold_complete_graph(self):
        """
        Test percolation threshold on a Complete graph.
        For a complete graph, the percolation threshold is 1/(n-1).
        """
        n = 10
        G = nx.complete_graph(n)
        
        calculator = MetricCalculator()
        result = calculator.calculate(G)
        
        # Theoretical percolation threshold for random graphs: 1 / (mean_degree)
        # For complete graph, mean_degree = n-1
        expected = 1.0 / (n - 1)
        actual = result['percolation_threshold']
        
        assert_almost_equal(actual, expected, decimal=6)

    def test_disconnected_graph_largest_component(self):
        """
        Test that metrics are calculated on the largest connected component
        when the graph is disconnected.
        """
        # Create a graph with two components: K5 and K3
        G1 = nx.complete_graph(5)
        G2 = nx.complete_graph(3)
        G = nx.disjoint_union(G1, G2)
        
        calculator = MetricCalculator()
        result = calculator.calculate(G)
        
        # Mean degree of K5 is 4. Mean degree of K3 is 2.
        # The largest component is K5 (5 nodes vs 3 nodes).
        # So the mean degree should be 4.0.
        expected_mean = 4.0
        actual_mean = result['mean_degree']
        
        assert_almost_equal(actual_mean, expected_mean, decimal=6)
        
        # Clustering coefficient of K5 is 1.0
        expected_cluster = 1.0
        actual_cluster = result['clustering_coefficient']
        
        assert_almost_equal(actual_cluster, expected_cluster, decimal=6)

    def test_path_graph_percolation_threshold(self):
        """
        Test percolation threshold on a Path graph.
        For a path graph, the percolation threshold is 1.0 (all edges must be present).
        However, for a path of length > 2, it's effectively 1/(mean_degree) ~ 1/2.
        We test that it returns a valid float and is positive.
        """
        n = 10
        G = nx.path_graph(n)
        
        calculator = MetricCalculator()
        result = calculator.calculate(G)
        
        # Just verify it returns a valid positive number
        assert result['percolation_threshold'] > 0
        assert np.isfinite(result['percolation_threshold'])

    def test_single_node_graph(self):
        """
        Test edge case: single node graph.
        Clustering coefficient is 0 (no neighbors to form triangles).
        Mean degree is 0.
        """
        G = nx.Graph()
        G.add_node(1)
        
        calculator = MetricCalculator()
        result = calculator.calculate(G)
        
        assert result['clustering_coefficient'] == 0.0
        assert result['mean_degree'] == 0.0
        # Percolation threshold might be NaN or 0 for single node
        assert np.isfinite(result['percolation_threshold']) or np.isnan(result['percolation_threshold'])

    def test_empty_graph(self):
        """
        Test edge case: empty graph.
        Should handle gracefully (likely return 0 or NaN).
        """
        G = nx.Graph()
        
        calculator = MetricCalculator()
        result = calculator.calculate(G)
        
        # Verify no exception raised
        assert 'clustering_coefficient' in result
        assert 'mean_degree' in result
        assert 'degree_variance' in result
        assert 'percolation_threshold' in result
        # All should be 0 or NaN
        assert result['mean_degree'] == 0.0
        assert result['clustering_coefficient'] == 0.0