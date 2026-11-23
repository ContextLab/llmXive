import pytest
import networkx as nx
import numpy as np
from scipy.stats import moment as scipy_moment
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics import MetricCalculator
from models import DefectGraph

class TestDegreeDistributionMoments:
    """Tests for T022: Degree Distribution Moments calculation."""

    def test_empty_graph_returns_zeros(self):
        """Test that empty graphs return 0.0 for mean and variance."""
        G = nx.Graph()
        # Add nodes but no edges to ensure it's not completely empty, 
        # but degree is 0 for all. Actually, let's test truly empty first.
        empty_graph = DefectGraph(networkx_graph=G, metadata={"snapshot_id": "empty"})
        
        calculator = MetricCalculator()
        results = calculator.calculate_degree_distribution_moments(empty_graph)
        
        assert results['mean'] == 0.0
        assert results['variance'] == 0.0

    def test_single_node_graph(self):
        """Test graph with a single node (degree 0)."""
        G = nx.Graph()
        G.add_node(0)
        graph = DefectGraph(networkx_graph=G, metadata={"snapshot_id": "single"})
        
        calculator = MetricCalculator()
        results = calculator.calculate_degree_distribution_moments(graph)
        
        # Mean degree of a single isolated node is 0
        assert results['mean'] == 0.0
        # Variance of [0] is 0
        assert results['variance'] == 0.0

    def test_complete_graph_moments(self):
        """Test K5 (complete graph with 5 nodes)."""
        # In K5, every node has degree 4.
        # Mean = 4, Variance = 0.
        G = nx.complete_graph(5)
        graph = DefectGraph(networkx_graph=G, metadata={"snapshot_id": "k5"})
        
        calculator = MetricCalculator()
        results = calculator.calculate_degree_distribution_moments(graph)
        
        expected_mean = 4.0
        expected_variance = 0.0
        
        assert abs(results['mean'] - expected_mean) < 1e-6
        assert abs(results['variance'] - expected_variance) < 1e-6

    def test_path_graph_moments(self):
        """Test a path graph P5 (1-2-3-4-5)."""
        # Degrees: [1, 2, 2, 2, 1]
        # Mean = (1+2+2+2+1)/5 = 8/5 = 1.6
        # Variance = E[(X - mu)^2]
        # = ((1-1.6)^2 + (2-1.6)^2 + (2-1.6)^2 + (2-1.6)^2 + (1-1.6)^2) / 5
        # = (0.36 + 0.16 + 0.16 + 0.16 + 0.36) / 5
        # = 1.2 / 5 = 0.24
        
        G = nx.path_graph(5)
        graph = DefectGraph(networkx_graph=G, metadata={"snapshot_id": "p5"})
        
        calculator = MetricCalculator()
        results = calculator.calculate_degree_distribution_moments(graph)
        
        expected_mean = 1.6
        expected_variance = 0.24
        
        assert abs(results['mean'] - expected_mean) < 1e-6
        assert abs(results['variance'] - expected_variance) < 1e-6

    def test_star_graph_moments(self):
        """Test a star graph S5 (center + 4 leaves)."""
        # Degrees: [4, 1, 1, 1, 1]
        # Mean = (4+1+1+1+1)/5 = 8/5 = 1.6
        # Variance calculation:
        # mu = 1.6
        # diffs: [2.4, -0.6, -0.6, -0.6, -0.6]
        # sq: [5.76, 0.36, 0.36, 0.36, 0.36]
        # sum = 7.2
        # var = 7.2 / 5 = 1.44
        
        G = nx.star_graph(4) # 5 nodes total (0 is center)
        graph = DefectGraph(networkx_graph=G, metadata={"snapshot_id": "s5"})
        
        calculator = MetricCalculator()
        results = calculator.calculate_degree_distribution_moments(graph)
        
        expected_mean = 1.6
        expected_variance = 1.44
        
        assert abs(results['mean'] - expected_mean) < 1e-6
        assert abs(results['variance'] - expected_variance) < 1e-6

    def test_custom_moments_list(self):
        """Test requesting specific moments."""
        G = nx.path_graph(10)
        graph = DefectGraph(networkx_graph=G, metadata={"snapshot_id": "custom"})
        
        calculator = MetricCalculator()
        # Request 1st and 3rd moments
        results = calculator.calculate_degree_distribution_moments(graph, moments=[1, 3])
        
        assert 'mean' in results
        assert 'moment_3' in results
        assert 'variance' not in results # 2nd moment not requested

    def test_matches_scipy_implementation(self):
        """Verify our variance calculation matches scipy.stats.moment exactly."""
        # Create a random graph
        G = nx.erdos_renyi_graph(50, 0.1, seed=42)
        degrees = np.array([d for n, d in G.degree()])
        
        expected_variance = float(scipy_moment(degrees, moment=2))
        
        graph = DefectGraph(networkx_graph=G, metadata={"snapshot_id": "random"})
        calculator = MetricCalculator()
        results = calculator.calculate_degree_distribution_moments(graph)
        
        assert abs(results['variance'] - expected_variance) < 1e-10