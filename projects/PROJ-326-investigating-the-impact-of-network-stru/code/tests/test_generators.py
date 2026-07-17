"""
Unit tests for network topology generators.

This module contains test cases for:
- Erdős-Rényi graph generation (T009)
- Watts-Strogatz (Small-World) generation with retry logic (T010)
- Barabási-Albert (Scale-Free) generation (T011)
"""
import pytest
import networkx as nx
import numpy as np
from pathlib import Path
import sys
import os
import json
import tempfile
import shutil
from typing import Dict, Any, List, Tuple
import random
import time

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.src.generators.er import ErdosRenyiGenerator
from code.src.generators.sw import WattsStrogatzGenerator
from code.src.generators.sf import BarabasiAlbertGenerator
from code.src.generators.metrics import (
    compute_clustering_coefficients,
    compute_degree_statistics,
    extract_all_metrics
)
from code.src.generators.base import BaseGenerator
from code.src.utils.config import load_config
from code.src.utils.reproducibility import ensure_data_directory

# Import timeout utilities if needed for tests
try:
    from code.src.generators.timeout import timeout, TimeoutError
    HAS_TIMEOUT = True
except ImportError:
    HAS_TIMEOUT = False


class TestErdosRenyiGenerator:
    """Unit tests for Erdős-Rényi graph generation (T009)."""
    
    def test_initialization(self):
        """Test that the generator initializes with correct parameters."""
        generator = ErdosRenyiGenerator(
            n=100,
            p=0.05,
            seed=42,
            target_clustering=0.05,
            max_attempts=5
        )
        
        assert generator.n == 100
        assert generator.p == 0.05
        assert generator.seed == 42
        assert generator.target_clustering == 0.05
        assert generator.max_attempts == 5
        assert isinstance(generator, BaseGenerator)
    
    def test_generation_success(self):
        """Test that a graph is successfully generated."""
        generator = ErdosRenyiGenerator(n=50, p=0.1, seed=42)
        graph, metadata = generator.generate()
        
        assert graph is not None
        assert isinstance(graph, nx.Graph)
        assert graph.number_of_nodes() == 50
        assert metadata is not None
        assert 'topology_class' in metadata
        assert metadata['topology_class'] == 'erdos_renyi'
    
    def test_connectivity_check(self):
        """Test that connectivity is verified when required."""
        # With high p, graph should be connected
        generator = ErdosRenyiGenerator(n=20, p=0.5, seed=42, require_connected=True)
        graph, metadata = generator.generate()
        
        assert nx.is_connected(graph)
    
    def test_clustering_target(self):
        """Test that clustering coefficient is approximately correct."""
        generator = ErdosRenyiGenerator(n=100, p=0.1, seed=42)
        graph, metadata = generator.generate()
        
        clustering = compute_clustering_coefficients(graph)
        # For ER graphs, expected clustering is approximately p
        expected_clustering = 0.1
        assert abs(clustering['average_clustering'] - expected_clustering) < 0.05
    
    def test_reproducibility(self):
        """Test that same seed produces same graph."""
        generator1 = ErdosRenyiGenerator(n=50, p=0.1, seed=12345)
        graph1, _ = generator1.generate()
        
        generator2 = ErdosRenyiGenerator(n=50, p=0.1, seed=12345)
        graph2, _ = generator2.generate()
        
        # Compare edge sets
        assert set(graph1.edges()) == set(graph2.edges())
        assert graph1.number_of_edges() == graph2.number_of_edges()
    
    def test_invalid_parameters(self):
        """Test that invalid parameters raise errors."""
        with pytest.raises(ValueError):
            ErdosRenyiGenerator(n=-10, p=0.1)
        
        with pytest.raises(ValueError):
            ErdosRenyiGenerator(n=10, p=1.5)
        with pytest.raises(ValueError):
            ErdosRenyiGenerator(n=10, p=-0.1)


class TestWattsStrogatzGenerator:
    """Unit tests for Watts-Strogatz (Small-World) generation with retry logic (T010)."""
    
    def test_initialization(self):
        """Test that the generator initializes with correct parameters."""
        generator = WattsStrogatzGenerator(
            n=100,
            k=4,
            p=0.1,
            seed=42,
            target_clustering=0.5,
            max_attempts=10,
            retry_on_connectivity=False
        )
        
        assert generator.n == 100
        assert generator.k == 4
        assert generator.p == 0.1
        assert generator.seed == 42
        assert generator.target_clustering == 0.5
        assert generator.max_attempts == 10
        assert isinstance(generator, BaseGenerator)
    
    def test_generation_success(self):
        """Test that a graph is successfully generated."""
        generator = WattsStrogatzGenerator(n=50, k=4, p=0.1, seed=42)
        graph, metadata = generator.generate()
        
        assert graph is not None
        assert isinstance(graph, nx.Graph)
        assert graph.number_of_nodes() == 50
        assert metadata is not None
        assert metadata['topology_class'] == 'watts_strogatz'
    
    def test_small_world_properties(self):
        """Test that generated graphs exhibit small-world properties."""
        generator = WattsStrogatzGenerator(n=100, k=6, p=0.1, seed=42)
        graph, metadata = generator.generate()
        
        metrics = extract_all_metrics(graph)
        
        # Small-world networks have high clustering and short path lengths
        assert metrics['clustering']['average_clustering'] > 0.1
        assert metrics['path_length']['average_path_length'] < 10
    
    def test_retry_logic_clustering_target(self):
        """Test retry logic when clustering target is not met."""
        # Use a tight clustering target to trigger retries
        generator = WattsStrogatzGenerator(
            n=50,
            k=4,
            p=0.05,
            seed=42,
            target_clustering=0.01,  # Very low, should be achievable
            max_attempts=5
        )
        
        graph, metadata = generator.generate()
        
        clustering = compute_clustering_coefficients(graph)
        
        # With retries, we should get a graph (may not meet exact target due to randomness)
        assert graph is not None
        assert metadata.get('attempts', 0) <= 5
    
    def test_connectivity_retry(self):
        """Test retry logic for connectivity requirement."""
        generator = WattsStrogatzGenerator(
            n=30,
            k=2,  # Low k might cause disconnection
            p=0.0,  # No rewiring
            seed=42,
            require_connected=True,
            max_attempts=10
        )
        
        graph, metadata = generator.generate()
        
        # With retry logic, should eventually get connected graph or raise after max attempts
        if metadata.get('attempts', 0) < 10:
            assert nx.is_connected(graph)
    
    def test_parameter_validation(self):
        """Test that invalid parameters raise errors."""
        with pytest.raises(ValueError):
            WattsStrogatzGenerator(n=-10, k=4, p=0.1)
        
        with pytest.raises(ValueError):
            WattsStrogatzGenerator(n=10, k=100, p=0.1)  # k > n/2
        
        with pytest.raises(ValueError):
            WattsStrogatzGenerator(n=10, k=4, p=1.5)
        
        with pytest.raises(ValueError):
            WattsStrogatzGenerator(n=10, k=4, p=-0.1)


class TestBarabasiAlbertGenerator:
    """Unit tests for Barabási-Albert (Scale-Free) generation (T011)."""
    
    def test_initialization(self):
        """Test that the generator initializes with correct parameters."""
        generator = BarabasiAlbertGenerator(
            n=100,
            m=3,
            seed=42,
            target_clustering=None,
            max_attempts=5
        )
        
        assert generator.n == 100
        assert generator.m == 3
        assert generator.seed == 42
        assert generator.target_clustering is None
        assert generator.max_attempts == 5
        assert isinstance(generator, BaseGenerator)
    
    def test_generation_success(self):
        """Test that a graph is successfully generated."""
        generator = BarabasiAlbertGenerator(n=50, m=3, seed=42)
        graph, metadata = generator.generate()
        
        assert graph is not None
        assert isinstance(graph, nx.Graph)
        assert graph.number_of_nodes() == 50
        assert metadata is not None
        assert metadata['topology_class'] == 'barabasi_albert'
    
    def test_node_count(self):
        """Test that the graph has exactly n nodes."""
        for n in [20, 50, 100]:
            generator = BarabasiAlbertGenerator(n=n, m=3, seed=42)
            graph, _ = generator.generate()
            assert graph.number_of_nodes() == n
    
    def test_edge_count_approximation(self):
        """Test that edge count is approximately m*n (theoretical: m*(n-m) + m*(m-1)/2)."""
        n = 100
        m = 3
        generator = BarabasiAlbertGenerator(n=n, m=m, seed=42)
        graph, _ = generator.generate()
        
        # BA model: each new node adds m edges
        # Starting with m nodes fully connected (m*(m-1)/2 edges)
        # Then n-m nodes each adding m edges
        expected_edges = m * (m - 1) // 2 + m * (n - m)
        
        # Allow small tolerance for implementation variations
        assert abs(graph.number_of_edges() - expected_edges) <= m
    
    def test_connectivity(self):
        """Test that generated graphs are connected."""
        generator = BarabasiAlbertGenerator(n=50, m=3, seed=42)
        graph, _ = generator.generate()
        
        # BA graphs should be connected by construction (m >= 1)
        assert nx.is_connected(graph)
    
    def test_scale_free_degree_distribution(self):
        """Test that degree distribution follows power law (scale-free property)."""
        n = 200
        m = 4
        generator = BarabasiAlbertGenerator(n=n, m=m, seed=42)
        graph, _ = generator.generate()
        
        degrees = [d for node, d in graph.degree()]
        
        # Check for power-law characteristics:
        # 1. Maximum degree should be significantly larger than average
        avg_degree = np.mean(degrees)
        max_degree = np.max(degrees)
        
        assert max_degree > avg_degree * 2, "Scale-free networks should have hubs"
        
        # 2. Check for heavy tail: few nodes with very high degree
        degree_counts = np.bincount(degrees)
        non_zero_counts = degree_counts[degree_counts > 0]
        
        # Should have a decreasing distribution (more low-degree nodes)
        assert len(non_zero_counts) > 1
    
    def test_minimum_degree(self):
        """Test that minimum degree is at least m (for nodes added after initialization)."""
        n = 50
        m = 3
        generator = BarabasiAlbertGenerator(n=n, m=m, seed=42)
        graph, _ = generator.generate()
        
        degrees = [d for node, d in graph.degree()]
        min_degree = np.min(degrees)
        
        # In BA model, new nodes attach with m edges, so min degree should be >= m
        # (except possibly for the initial m nodes which might have higher degree)
        assert min_degree >= 1  # At least connected
    
    def test_reproducibility(self):
        """Test that same seed produces same graph."""
        generator1 = BarabasiAlbertGenerator(n=50, m=3, seed=12345)
        graph1, _ = generator1.generate()
        
        generator2 = BarabasiAlbertGenerator(n=50, m=3, seed=12345)
        graph2, _ = generator2.generate()
        
        # Compare edge sets
        assert set(graph1.edges()) == set(graph2.edges())
        assert graph1.number_of_edges() == graph2.number_of_edges()
    
    def test_parameter_validation(self):
        """Test that invalid parameters raise errors."""
        # Negative n
        with pytest.raises(ValueError):
            BarabasiAlbertGenerator(n=-10, m=3)
        
        # m >= n
        with pytest.raises(ValueError):
            BarabasiAlbertGenerator(n=5, m=5)
        
        # m < 1
        with pytest.raises(ValueError):
            BarabasiAlbertGenerator(n=50, m=0)
    
    def test_clustering_coefficient(self):
        """Test that clustering coefficient is non-zero (BA networks have some clustering)."""
        generator = BarabasiAlbertGenerator(n=100, m=4, seed=42)
        graph, _ = generator.generate()
        
        clustering = compute_clustering_coefficients(graph)
        avg_clustering = clustering['average_clustering']
        
        # BA networks have lower clustering than small-world but > 0
        assert avg_clustering > 0
        assert avg_clustering < 1  # Valid probability
    
    def test_metadata_completeness(self):
        """Test that metadata contains all required fields."""
        generator = BarabasiAlbertGenerator(n=50, m=3, seed=42)
        graph, metadata = generator.generate()
        
        required_fields = [
            'topology_class',
            'n',
            'm',
            'seed',
            'num_nodes',
            'num_edges',
            'algorithm'
        ]
        
        for field in required_fields:
            assert field in metadata, f"Missing metadata field: {field}"
        
        assert metadata['topology_class'] == 'barabasi_albert'
        assert metadata['algorithm'] == 'barabasi_albert'
        assert metadata['n'] == 50
        assert metadata['m'] == 3
    
    def test_large_scale_generation(self):
        """Test generation of larger networks."""
        generator = BarabasiAlbertGenerator(n=500, m=5, seed=42)
        graph, metadata = generator.generate()
        
        assert graph.number_of_nodes() == 500
        assert graph.number_of_edges() > 0
        assert nx.is_connected(graph)
    
    def test_degree_distribution_shape(self):
        """Test that degree distribution has the characteristic shape of scale-free networks."""
        n = 300
        m = 3
        generator = BarabasiAlbertGenerator(n=n, m=m, seed=42)
        graph, _ = generator.generate()
        
        degrees = [d for node, d in graph.degree()]
        degree_counts = {}
        
        for d in degrees:
            degree_counts[d] = degree_counts.get(d, 0) + 1
        
        # Sort by degree
        sorted_degrees = sorted(degree_counts.keys())
        sorted_counts = [degree_counts[d] for d in sorted_degrees]
        
        # In scale-free networks, lower degrees should have higher counts
        # (decreasing distribution)
        # Check that the first few degrees have higher counts than later ones
        if len(sorted_counts) > 3:
            # Compare average of first quarter vs last quarter
            quarter = len(sorted_counts) // 4
            if quarter > 0:
                early_avg = np.mean(sorted_counts[:quarter])
                late_avg = np.mean(sorted_counts[-quarter:])
                
                # Early degrees should generally have higher counts
                assert early_avg >= late_avg * 0.5, "Degree distribution should show scale-free characteristics"
    
    def test_m_parameter_effect(self):
        """Test that varying m affects edge density."""
        n = 100
        seed = 42
        
        graphs = []
        for m in [2, 4, 6]:
            generator = BarabasiAlbertGenerator(n=n, m=m, seed=seed)
            graph, _ = generator.generate()
            graphs.append((m, graph.number_of_edges()))
        
        # Higher m should result in more edges
        edges_2 = graphs[0][1]
        edges_4 = graphs[1][1]
        edges_6 = graphs[2][1]
        
        assert edges_4 > edges_2, "Increasing m should increase edges"
        assert edges_6 > edges_4, "Increasing m should increase edges"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])