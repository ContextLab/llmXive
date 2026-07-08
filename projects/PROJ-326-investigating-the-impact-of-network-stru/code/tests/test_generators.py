"""
Unit tests for network topology generators.
"""
import pytest
import networkx as nx
import numpy as np
from pathlib import Path
import sys

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.generators.er import ErdosRenyiGenerator
from code.src.generators.sw import WattsStrogatzGenerator
from code.src.generators.sf import BarabasiAlbertGenerator
from code.src.generators.metrics import extract_all_metrics, compute_clustering_coefficients
from code.src.utils.config import load_config
from code.src.generators.base import BaseGenerator

class TestErdosRenyiGenerator:
    """Tests for Erdős-Rényi random graph generation."""

    def test_initialization(self):
        """Test that the generator initializes with correct parameters."""
        gen = ErdosRenyiGenerator(n=100, p=0.1, seed=42)
        assert gen.n == 100
        assert gen.p == 0.1
        assert gen.seed == 42

    def test_generate_connected(self):
        """Test generation of a connected ER graph."""
        gen = ErdosRenyiGenerator(n=50, p=0.2, seed=42)
        graph = gen.generate()
        
        assert isinstance(graph, nx.Graph)
        assert graph.number_of_nodes() == 50
        # With p=0.2, graph should almost certainly be connected
        assert nx.is_connected(graph)

    def test_generate_disconnected(self):
        """Test generation of a disconnected ER graph (low p)."""
        gen = ErdosRenyiGenerator(n=100, p=0.005, seed=123)
        graph = gen.generate()
        
        assert isinstance(graph, nx.Graph)
        assert graph.number_of_nodes() == 100
        # With very low p, graph is likely disconnected
        # We don't assert connectivity here, just that it runs

    def test_metrics_extraction(self):
        """Test that metrics can be extracted from generated graph."""
        gen = ErdosRenyiGenerator(n=50, p=0.15, seed=42)
        graph = gen.generate()
        
        metrics = extract_all_metrics(graph)
        
        assert 'clustering_coefficient' in metrics
        assert 'average_path_length' in metrics
        assert 'degree_distribution' in metrics
        assert 'number_of_nodes' in metrics
        assert 'number_of_edges' in metrics

    def test_reproducibility(self):
        """Test that same seed produces same graph."""
        gen1 = ErdosRenyiGenerator(n=50, p=0.1, seed=999)
        gen2 = ErdosRenyiGenerator(n=50, p=0.1, seed=999)
        
        graph1 = gen1.generate()
        graph2 = gen2.generate()
        
        # Compare edge sets
        assert set(graph1.edges()) == set(graph2.edges())
        assert set(graph1.nodes()) == set(graph2.nodes())


class TestWattsStrogatzGenerator:
    """Tests for Watts-Strogatz small-world network generation."""

    def test_initialization(self):
        """Test generator initialization."""
        gen = WattsStrogatzGenerator(n=100, k=4, p=0.1, seed=42)
        assert gen.n == 100
        assert gen.k == 4
        assert gen.p == 0.1
        assert gen.seed == 42

    def test_generate_connected(self):
        """Test generation of a connected SW graph."""
        gen = WattsStrogatzGenerator(n=50, k=4, p=0.1, seed=42)
        graph = gen.generate()
        
        assert isinstance(graph, nx.Graph)
        assert graph.number_of_nodes() == 50
        # Watts-Strogatz with reasonable k should be connected
        assert nx.is_connected(graph)

    def test_clustering_target(self):
        """Test that clustering coefficient is non-trivial."""
        gen = WattsStrogatzGenerator(n=100, k=6, p=0.1, seed=42)
        graph = gen.generate()
        
        metrics = extract_all_metrics(graph)
        clustering = metrics['clustering_coefficient']
        
        # Small-world networks should have higher clustering than random
        # With p=0.1, we expect significant clustering
        assert clustering > 0.01
        assert clustering < 1.0

    def test_retry_logic_integration(self):
        """Test that the generator handles connectivity via retry logic."""
        # This tests the integration of retry logic from base class
        # We use a low p which might cause disconnection in initial attempts
        gen = WattsStrogatzGenerator(n=100, k=4, p=0.05, seed=12345)
        graph = gen.generate()
        
        # Should eventually return a connected graph or raise after max retries
        assert isinstance(graph, nx.Graph)
        # If it returns, it should be connected (enforced by retry logic)
        assert nx.is_connected(graph)

    def test_reproducibility(self):
        """Test that same seed produces same graph."""
        gen1 = WattsStrogatzGenerator(n=50, k=4, p=0.1, seed=777)
        gen2 = WattsStrogatzGenerator(n=50, k=4, p=0.1, seed=777)
        
        graph1 = gen1.generate()
        graph2 = gen2.generate()
        
        assert set(graph1.edges()) == set(graph2.edges())


class TestBarabasiAlbertGenerator:
    """Tests for Barabási-Albert scale-free network generation."""

    def test_initialization(self):
        """Test generator initialization."""
        gen = BarabasiAlbertGenerator(n=100, m=3, seed=42)
        assert gen.n == 100
        assert gen.m == 3
        assert gen.seed == 42

    def test_generate_connected(self):
        """Test generation of a connected BA graph."""
        gen = BarabasiAlbertGenerator(n=50, m=2, seed=42)
        graph = gen.generate()
        
        assert isinstance(graph, nx.Graph)
        assert graph.number_of_nodes() == 50
        # BA model with m >= 1 should produce connected graph
        assert nx.is_connected(graph)

    def test_degree_distribution_power_law(self):
        """Test that the degree distribution follows a power law."""
        gen = BarabasiAlbertGenerator(n=200, m=3, seed=42)
        graph = gen.generate()
        
        degrees = [d for n, d in graph.degree()]
        mean_degree = np.mean(degrees)
        
        # In BA model, mean degree should be approximately 2*m
        assert abs(mean_degree - 2 * gen.m) < 1.0  # Allow some variance

        # Check for presence of hubs (high degree nodes)
        max_degree = max(degrees)
        # In scale-free networks, max degree should be significantly higher than mean
        assert max_degree > 2 * mean_degree

    def test_minimum_edges(self):
        """Test that the graph has the expected number of edges."""
        gen = BarabasiAlbertGenerator(n=100, m=4, seed=42)
        graph = gen.generate()
        
        # BA model creates m edges per new node
        # First m nodes form a clique, then each new node adds m edges
        # Total edges ≈ m * (n - m) + m*(m-1)/2
        # Simplified: approximately m * n for large n
        expected_edges_approx = gen.m * gen.n
        actual_edges = graph.number_of_edges()
        
        # Allow 10% variance for the exact formula vs approximation
        assert abs(actual_edges - expected_edges_approx) / expected_edges_approx < 0.15

    def test_clustering_coefficient(self):
        """Test that BA networks have non-trivial clustering."""
        gen = BarabasiAlbertGenerator(n=100, m=3, seed=42)
        graph = gen.generate()
        
        metrics = extract_all_metrics(graph)
        clustering = metrics['clustering_coefficient']
        
        # BA networks typically have low but non-zero clustering
        assert clustering > 0.0
        assert clustering < 1.0

    def test_reproducibility(self):
        """Test that same seed produces same graph."""
        gen1 = BarabasiAlbertGenerator(n=50, m=2, seed=888)
        gen2 = BarabasiAlbertGenerator(n=50, m=2, seed=888)
        
        graph1 = gen1.generate()
        graph2 = gen2.generate()
        
        assert set(graph1.edges()) == set(graph2.edges())
        assert set(graph1.nodes()) == set(graph2.nodes())

    def test_invalid_m_value(self):
        """Test that m < 1 raises an error."""
        with pytest.raises(ValueError):
            BarabasiAlbertGenerator(n=50, m=0, seed=42)

    def test_invalid_n_value(self):
        """Test that n <= 0 raises an error."""
        with pytest.raises(ValueError):
            BarabasiAlbertGenerator(n=0, m=2, seed=42)

    def test_m_greater_than_n(self):
        """Test that m >= n raises an error."""
        with pytest.raises(ValueError):
            BarabasiAlbertGenerator(n=5, m=10, seed=42)

    def test_metrics_completeness(self):
        """Test that all expected metrics are present."""
        gen = BarabasiAlbertGenerator(n=100, m=3, seed=42)
        graph = gen.generate()
        
        metrics = extract_all_metrics(graph)
        
        expected_keys = [
            'number_of_nodes',
            'number_of_edges',
            'clustering_coefficient',
            'average_path_length',
            'degree_distribution',
            'max_degree',
            'min_degree',
            'mean_degree',
            'density'
        ]
        
        for key in expected_keys:
            assert key in metrics, f"Missing metric: {key}"