"""
Unit tests for Erdős-Rényi graph generation (User Story 1).

This test suite verifies that the ER generator:
1. Produces connected graphs as expected.
2. Generates graphs with the correct number of nodes.
3. Produces edge counts consistent with the theoretical probability p.
4. Integrates correctly with the project's configuration and logging utilities.
"""
import pytest
import networkx as nx
import numpy as np
from pathlib import Path
import sys

# Ensure project root is in path for imports
# Note: In a real execution environment, this might be handled by PYTHONPATH or setup.py
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.generators.er import ErdosRenyiGenerator
from code.src.generators.sf import BarabasiAlbertGenerator
from code.src.utils.config import load_config


class TestErdosRenyiGeneration:
    """Tests for the Erdős-Renyi generator implementation."""

    @pytest.fixture
    def config(self):
        """Load the project configuration."""
        # Assuming config.yaml exists in the code directory as per T004
        config_path = Path(__file__).parent.parent / "config.yaml"
        if not config_path.exists():
            pytest.skip("config.yaml not found; skipping configuration-dependent tests.")
        return load_config(config_path)

    def test_generator_instantiation(self, config):
        """Test that the generator can be instantiated with valid parameters."""
        generator = ErdosRenyiGenerator(
            n_nodes=100,
            p_edge=0.1,
            seed=42,
            config=config
        )
        assert generator.n_nodes == 100
        assert generator.p_edge == 0.1
        assert generator.seed == 42

    def test_generate_connected_graph(self, config):
        """Test that the generator produces a connected graph."""
        generator = ErdosRenyiGenerator(
            n_nodes=50,
            p_edge=0.2, # High probability to ensure connectivity
            seed=42,
            config=config
        )
        
        # Generate a single graph
        graph = generator.generate()
        
        assert graph is not None
        assert isinstance(graph, nx.Graph)
        assert nx.is_connected(graph)
        assert graph.number_of_nodes() == 50

    def test_generate_batch_connectivity(self, config):
        """Test that a batch of graphs are generated and connectivity is checked."""
        generator = ErdosRenyiGenerator(
            n_nodes=30,
            p_edge=0.3,
            seed=123,
            config=config
        )
        
        # Generate a batch
        graphs = generator.generate_batch(count=5)
        
        assert len(graphs) == 5
        for i, graph in enumerate(graphs):
            assert graph is not None
            assert graph.number_of_nodes() == 30
            # With p=0.3 and n=30, connectivity is very likely, but we assert it
            # If the generator's retry logic fails to find a connected graph, it should raise or return None
            # We assume the generator handles retries internally as per T016/T013 specs
            if graph is not None:
                assert nx.is_connected(graph), f"Graph {i} in batch is not connected"

    def test_edge_count_statistics(self, config):
        """Test that the number of edges approximates the theoretical expectation."""
        n = 100
        p = 0.05
        expected_edges = n * (n - 1) / 2 * p
        
        generator = ErdosRenyiGenerator(
            n_nodes=n,
            p_edge=p,
            seed=999,
            config=config
        )
        
        # Generate multiple graphs to check average edge count
        num_trials = 20
        total_edges = 0
        connected_count = 0
        
        for _ in range(num_trials):
            g = generator.generate()
            if g is not None and nx.is_connected(g):
                total_edges += g.number_of_edges()
                connected_count += 1
        
        if connected_count == 0:
            pytest.fail("No connected graphs generated in test; p might be too low for n.")
        
        avg_edges = total_edges / connected_count
        
        # Allow a 20% tolerance for stochastic variation
        tolerance = 0.20 * expected_edges
        assert abs(avg_edges - expected_edges) <= tolerance, \
            f"Average edges {avg_edges:.2f} deviates significantly from expected {expected_edges:.2f}"

    def test_seed_reproducibility(self, config):
        """Test that using the same seed produces the same graph."""
        generator1 = ErdosRenyiGenerator(n_nodes=20, p_edge=0.3, seed=555, config=config)
        generator2 = ErdosRenyiGenerator(n_nodes=20, p_edge=0.3, seed=555, config=config)
        
        g1 = generator1.generate()
        g2 = generator2.generate()
        
        assert g1 is not None
        assert g2 is not None
        
        # Compare edges
        edges1 = set(tuple(sorted(e)) for e in g1.edges())
        edges2 = set(tuple(sorted(e)) for e in g2.edges())
        
        assert edges1 == edges2, "Graphs generated with the same seed should be identical"

    def test_invalid_probability_raises(self, config):
        """Test that invalid p_edge values raise appropriate errors or are handled."""
        # The generator should handle p > 1 or p < 0 gracefully or raise ValueError
        # Depending on implementation, we test for expected behavior
        with pytest.raises((ValueError, AssertionError)):
            ErdosRenyiGenerator(n_nodes=10, p_edge=1.5, seed=1, config=config)

    def test_node_count_precision(self, config):
        """Verify the exact number of nodes matches the input."""
        test_sizes = [10, 50, 100, 200]
        for n in test_sizes:
            generator = ErdosRenyiGenerator(n_nodes=n, p_edge=0.1, seed=1, config=config)
            g = generator.generate()
            assert g.number_of_nodes() == n, f"Expected {n} nodes, got {g.number_of_nodes()}"


class TestBarabasiAlbertGeneration:
    """Tests for the Barabási-Albert (Scale-Free) generator implementation."""

    @pytest.fixture
    def config(self):
        """Load the project configuration."""
        config_path = Path(__file__).parent.parent / "config.yaml"
        if not config_path.exists():
            pytest.skip("config.yaml not found; skipping configuration-dependent tests.")
        return load_config(config_path)

    def test_generator_instantiation(self, config):
        """Test that the BA generator can be instantiated with valid parameters."""
        generator = BarabasiAlbertGenerator(
            n_nodes=100,
            m_edges=3,
            seed=42,
            config=config
        )
        assert generator.n_nodes == 100
        assert generator.m_edges == 3
        assert generator.seed == 42

    def test_generate_connected_graph(self, config):
        """Test that the generator produces a connected graph."""
        # BA graphs are naturally connected if m >= 1 and n > m
        generator = BarabasiAlbertGenerator(
            n_nodes=50,
            m_edges=3,
            seed=42,
            config=config
        )
        
        graph = generator.generate()
        
        assert graph is not None
        assert isinstance(graph, nx.Graph)
        assert nx.is_connected(graph)
        assert graph.number_of_nodes() == 50

    def test_min_degree_constraint(self, config):
        """Test that the minimum degree in the generated graph is at least m."""
        m = 3
        generator = BarabasiAlbertGenerator(
            n_nodes=100,
            m_edges=m,
            seed=123,
            config=config
        )
        
        graph = generator.generate()
        
        assert graph is not None
        degrees = [d for _, d in graph.degree()]
        min_degree = min(degrees)
        
        # In a standard BA model, the minimum degree should be at least m
        # (though strictly speaking, the initial m0 nodes might have degree m,
        # and new nodes attach with m edges, so min degree is m)
        assert min_degree >= m, f"Minimum degree {min_degree} is less than m={m}"

    def test_scale_free_property(self, config):
        """
        Test that the degree distribution follows a power law (scale-free property).
        We check that the degree distribution is not uniform and has a long tail.
        """
        generator = BarabasiAlbertGenerator(
            n_nodes=200,
            m_edges=2,
            seed=456,
            config=config
        )
        
        graph = generator.generate()
        degrees = [d for _, d in graph.degree()]
        
        # Calculate mean and max degree
        mean_degree = np.mean(degrees)
        max_degree = max(degrees)
        
        # In a scale-free network, max degree should be significantly larger than mean
        # This is a heuristic check, not a rigorous statistical test
        assert max_degree > mean_degree * 2, \
            f"Max degree {max_degree} is not significantly larger than mean {mean_degree:.2f}"
        
        # Check for presence of hubs (nodes with degree > 2 * mean)
        hubs = [d for d in degrees if d > 2 * mean_degree]
        assert len(hubs) > 0, "No hubs found in the generated graph"

    def test_seed_reproducibility(self, config):
        """Test that using the same seed produces the same graph."""
        generator1 = BarabasiAlbertGenerator(n_nodes=30, m_edges=2, seed=789, config=config)
        generator2 = BarabasiAlbertGenerator(n_nodes=30, m_edges=2, seed=789, config=config)
        
        g1 = generator1.generate()
        g2 = generator2.generate()
        
        assert g1 is not None
        assert g2 is not None
        
        # Compare edges
        edges1 = set(tuple(sorted(e)) for e in g1.edges())
        edges2 = set(tuple(sorted(e)) for e in g2.edges())
        
        assert edges1 == edges2, "Graphs generated with the same seed should be identical"

    def test_invalid_m_edges_raises(self, config):
        """Test that invalid m_edges values raise appropriate errors."""
        # m must be >= 1 and < n_nodes
        with pytest.raises((ValueError, AssertionError)):
            BarabasiAlbertGenerator(n_nodes=10, m_edges=0, seed=1, config=config)
        
        with pytest.raises((ValueError, AssertionError)):
            BarabasiAlbertGenerator(n_nodes=5, m_edges=5, seed=1, config=config)

    def test_node_count_precision(self, config):
        """Verify the exact number of nodes matches the input."""
        test_sizes = [20, 50, 100, 200]
        m = 2
        for n in test_sizes:
            generator = BarabasiAlbertGenerator(n_nodes=n, m_edges=m, seed=1, config=config)
            g = generator.generate()
            assert g.number_of_nodes() == n, f"Expected {n} nodes, got {g.number_of_nodes()}"

    def test_edge_count_approximation(self, config):
        """
        Test that the number of edges is approximately m * (n - m0).
        In the standard BA model starting with m0=m nodes, each new node adds m edges.
        Total edges ≈ m * (n - m).
        """
        n = 100
        m = 3
        expected_edges = m * (n - m)
        
        generator = BarabasiAlbertGenerator(
            n_nodes=n,
            m_edges=m,
            seed=999,
            config=config
        )
        
        graph = generator.generate()
        actual_edges = graph.number_of_edges()
        
        # Allow some tolerance due to implementation details (e.g., initial graph size)
        # The theoretical minimum is m*(n-m), but some implementations might vary slightly
        # We check that it's close to the expected value
        tolerance = 0.10 * expected_edges
        assert abs(actual_edges - expected_edges) <= tolerance, \
            f"Edge count {actual_edges} deviates significantly from expected {expected_edges}"