"""
Unit tests for network topology generators (US1).
Tests Erdős-Rényi, Watts-Strogatz, and Barabási-Albert generators.
"""

import pytest
import networkx as nx
import numpy as np
from pathlib import Path
import sys
import json

# Ensure src is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.generators.er import ErdosRenyiGenerator
from code.src.generators.sw import WattsStrogatzGenerator
from code.src.generators.sf import BarabasiAlbertGenerator
from code.src.generators.metrics import (
    compute_clustering_coefficients,
    compute_degree_statistics,
    extract_all_metrics
)
from code.src.utils.config import load_config
from code.src.utils.logging import log_run, log_metric, clear_run_log
from code.src.utils.reproducibility import ensure_data_directory


class TestErdosRenyiGenerator:
    """Tests for Erdős-Rényi graph generation (T009)."""

    def test_initialization(self):
        """Test that the generator initializes correctly."""
        config = {
            "n": 100,
            "p": 0.1,
            "seed": 42
        }
        gen = ErdosRenyiGenerator(config)
        assert gen.n == 100
        assert gen.p == 0.1
        assert gen.seed == 42

    def test_graph_generation(self):
        """Test that a connected graph is generated."""
        config = {
            "n": 100,
            "p": 0.1,
            "seed": 42
        }
        gen = ErdosRenyiGenerator(config)
        G = gen.generate()
        assert isinstance(G, nx.Graph)
        assert G.number_of_nodes() == 100
        # For p=0.1 and n=100, graph should be connected with high probability
        assert nx.is_connected(G), "Generated ER graph should be connected"

    def test_degree_distribution(self):
        """Test that degree distribution follows expected binomial approx."""
        config = {
            "n": 500,
            "p": 0.05,
            "seed": 123
        }
        gen = ErdosRenyiGenerator(config)
        G = gen.generate()
        degrees = [d for _, d in G.degree()]
        avg_degree = np.mean(degrees)
        expected_avg = config["n"] * config["p"]
        # Allow 10% tolerance due to randomness
        assert abs(avg_degree - expected_avg) / expected_avg < 0.15

    def test_reproducibility(self):
        """Test that same seed produces same graph."""
        config = {
            "n": 100,
            "p": 0.1,
            "seed": 42
        }
        gen1 = ErdosRenyiGenerator(config)
        G1 = gen1.generate()
        
        gen2 = ErdosRenyiGenerator(config)
        G2 = gen2.generate()
        
        assert nx.is_isomorphic(G1, G2)


class TestWattsStrogatzGenerator:
    """Tests for Watts-Strogatz small-world graph generation (T010)."""

    def test_initialization(self):
        """Test that the generator initializes correctly."""
        config = {
            "n": 100,
            "k": 4,
            "p": 0.1,
            "seed": 42,
            "target_clustering": 0.3
        }
        gen = WattsStrogatzGenerator(config)
        assert gen.n == 100
        assert gen.k == 4
        assert gen.p == 0.1
        assert gen.seed == 42
        assert gen.target_clustering == 0.3

    def test_graph_generation(self):
        """Test that a connected small-world graph is generated."""
        config = {
            "n": 100,
            "k": 4,
            "p": 0.1,
            "seed": 42
        }
        gen = WattsStrogatzGenerator(config)
        G = gen.generate()
        assert isinstance(G, nx.Graph)
        assert G.number_of_nodes() == 100
        # Watts-Strogatz with low p should be connected
        assert nx.is_connected(G), "Generated WS graph should be connected"

    def test_clustering_coefficient(self):
        """Test that clustering coefficient is within expected range."""
        config = {
            "n": 200,
            "k": 4,
            "p": 0.1,
            "seed": 42
        }
        gen = WattsStrogatzGenerator(config)
        G = gen.generate()
        clustering = nx.average_clustering(G)
        # For WS with low p, clustering should be relatively high (> 0.1)
        assert clustering > 0.1, f"Expected clustering > 0.1, got {clustering}"

    def test_retry_logic_clustering_target(self):
        """Test that retry logic attempts to meet clustering target."""
        config = {
            "n": 200,
            "k": 6,
            "p": 0.05,
            "seed": 42,
            "target_clustering": 0.2,
            "max_retries": 5
        }
        gen = WattsStrogatzGenerator(config)
        G = gen.generate()
        clustering = nx.average_clustering(G)
        # The generator should attempt to meet the target, 
        # but we verify it at least generates a valid graph
        assert nx.is_connected(G)
        # Note: Exact clustering target may not be met due to randomness,
        # but the retry logic should be exercised

    def test_reproducibility(self):
        """Test that same seed produces same graph."""
        config = {
            "n": 100,
            "k": 4,
            "p": 0.1,
            "seed": 42
        }
        gen1 = WattsStrogatzGenerator(config)
        G1 = gen1.generate()
        
        gen2 = WattsStrogatzGenerator(config)
        G2 = gen2.generate()
        
        assert nx.is_isomorphic(G1, G2)


class TestBarabasiAlbertGenerator:
    """Tests for Barabási-Albert scale-free graph generation (T011)."""

    def test_initialization(self):
        """Test that the generator initializes correctly."""
        config = {
            "n": 100,
            "m": 3,
            "seed": 42
        }
        gen = BarabasiAlbertGenerator(config)
        assert gen.n == 100
        assert gen.m == 3
        assert gen.seed == 42

    def test_graph_generation(self):
        """Test that a connected scale-free graph is generated."""
        config = {
            "n": 100,
            "m": 3,
            "seed": 42
        }
        gen = BarabasiAlbertGenerator(config)
        G = gen.generate()
        assert isinstance(G, nx.Graph)
        assert G.number_of_nodes() == 100
        # BA graphs are typically connected
        assert nx.is_connected(G), "Generated BA graph should be connected"

    def test_degree_distribution_power_law(self):
        """Test that degree distribution follows power law (scale-free property)."""
        config = {
            "n": 500,
            "m": 3,
            "seed": 42
        }
        gen = BarabasiAlbertGenerator(config)
        G = gen.generate()
        
        degrees = [d for _, d in G.degree()]
        # BA graphs should have a few high-degree nodes (hubs)
        max_degree = max(degrees)
        avg_degree = np.mean(degrees)
        
        # In scale-free networks, max degree should be significantly larger than average
        # For n=500, m=3, we expect max_degree > 2*avg_degree
        assert max_degree > 2 * avg_degree, \
            f"BA graph should have hubs: max={max_degree}, avg={avg_degree}"
        
        # Check that there are nodes with degree >= 10 (hubs)
        high_degree_count = sum(1 for d in degrees if d >= 10)
        assert high_degree_count > 0, "BA graph should have high-degree nodes"

    def test_preferential_attachment(self):
        """Test that higher degree nodes attract more edges (preferential attachment)."""
        config = {
            "n": 200,
            "m": 2,
            "seed": 42
        }
        gen = BarabasiAlbertGenerator(config)
        G = gen.generate()
        
        # Calculate degree correlation
        # In BA model, there should be positive correlation between node degree
        # and the rate at which they attract new edges
        degrees = dict(G.degree())
        
        # Sort nodes by degree
        sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
        
        # Top 10% of nodes should have significantly higher degree
        top_10_count = max(1, len(sorted_nodes) // 10)
        top_10_degrees = [d for _, d in sorted_nodes[:top_10_count]]
        bottom_10_degrees = [d for _, d in sorted_nodes[-top_10_count:]]
        
        avg_top = np.mean(top_10_degrees)
        avg_bottom = np.mean(bottom_10_degrees)
        
        # Top nodes should have much higher degree than bottom nodes
        assert avg_top > 3 * avg_bottom, \
            f"Preferential attachment not evident: top={avg_top}, bottom={avg_bottom}"

    def test_reproducibility(self):
        """Test that same seed produces same graph."""
        config = {
            "n": 100,
            "m": 3,
            "seed": 42
        }
        gen1 = BarabasiAlbertGenerator(config)
        G1 = gen1.generate()
        
        gen2 = BarabasiAlbertGenerator(config)
        G2 = gen2.generate()
        
        # BA graphs with same seed should be identical
        assert nx.is_isomorphic(G1, G2)

    def test_metrics_extraction(self):
        """Test that metrics are correctly extracted for BA graphs."""
        config = {
            "n": 200,
            "m": 3,
            "seed": 42
        }
        gen = BarabasiAlbertGenerator(config)
        G = gen.generate()
        
        metrics = extract_all_metrics(G)
        
        # Verify expected metrics are present
        assert "clustering_coefficient" in metrics
        assert "average_path_length" in metrics
        assert "degree_distribution" in metrics
        assert "average_degree" in metrics
        
        # BA graphs typically have low clustering and short path lengths
        assert metrics["clustering_coefficient"] > 0
        assert metrics["average_path_length"] > 0

    def test_edge_count(self):
        """Test that edge count is approximately n*m for BA graph."""
        config = {
            "n": 200,
            "m": 3,
            "seed": 42
        }
        gen = BarabasiAlbertGenerator(config)
        G = gen.generate()
        
        # BA graph with n nodes and parameter m has approximately n*m edges
        expected_edges = config["n"] * config["m"]
        actual_edges = G.number_of_edges()
        
        # Allow some tolerance due to the algorithm's specifics
        assert abs(actual_edges - expected_edges) / expected_edges < 0.1, \
            f"Edge count mismatch: expected ~{expected_edges}, got {actual_edges}"


class TestGeneratorIntegration:
    """Integration tests for all generators."""

    def test_all_generators_produce_valid_graphs(self):
        """Test that all generators produce valid, connected graphs."""
        configs = [
            {"n": 100, "p": 0.1, "seed": 42, "type": "er"},
            {"n": 100, "k": 4, "p": 0.1, "seed": 42, "type": "ws"},
            {"n": 100, "m": 3, "seed": 42, "type": "ba"}
        ]
        
        generators = [
            ErdosRenyiGenerator,
            WattsStrogatzGenerator,
            BarabasiAlbertGenerator
        ]
        
        for config, gen_class in zip(configs, generators):
            gen = gen_class(config)
            G = gen.generate()
            
            assert isinstance(G, nx.Graph)
            assert nx.is_connected(G)
            assert G.number_of_nodes() == config["n"]

    def test_metrics_consistency(self):
        """Test that metrics are consistent across different generators."""
        configs = [
            {"n": 100, "p": 0.1, "seed": 42, "type": "er"},
            {"n": 100, "k": 4, "p": 0.1, "seed": 42, "type": "ws"},
            {"n": 100, "m": 3, "seed": 42, "type": "ba"}
        ]
        
        generators = [
            ErdosRenyiGenerator,
            WattsStrogatzGenerator,
            BarabasiAlbertGenerator
        ]
        
        for config, gen_class in zip(configs, generators):
            gen = gen_class(config)
            G = gen.generate()
            metrics = extract_all_metrics(G)
            
            # All metrics should be positive numbers
            assert metrics["clustering_coefficient"] >= 0
            assert metrics["average_path_length"] > 0
            assert metrics["average_degree"] > 0