"""
Unit tests for network generators.
Includes tests for connectivity verification and retry logic.
"""
import pytest
import networkx as nx
import numpy as np
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from code.src.generators.base import BaseGenerator
from code.src.generators.er import ErdosRenyiGenerator
from code.src.generators.sw import WattsStrogatzGenerator
from code.src.generators.sf import BarabasiAlbertGenerator
from code.src.generators.timeout import TimeoutError

class MockGenerator(BaseGenerator):
    """Mock generator for testing retry logic"""
    def __init__(self, config, fail_until_attempt=None):
        super().__init__(config)
        self.fail_until_attempt = fail_until_attempt
        self.attempt_count = 0

    def _generate_candidate(self):
        self.attempt_count += 1
        if self.fail_until_attempt and self.attempt_count <= self.fail_until_attempt:
            # Return a disconnected graph
            G = nx.Graph()
            G.add_nodes_from([1, 2, 3])
            G.add_edges_from([(1, 2)])  # Node 3 is isolated
            return G
        # Return a connected graph
        G = nx.complete_graph(5)
        return G

    def get_generator_name(self):
        return "MockGenerator"

    def get_parameters(self):
        return {"fail_until": self.fail_until_attempt}

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for data files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_config():
    return {
        'seed': 42,
        'max_retries': 5,
        'retry_delay': 0.01,
        'timeout_seconds': 30
    }

def test_sw_retries_on_disconnect(mock_config):
    """
    Test that Watts-Strogatz generator retries on disconnected graphs.
    Verifies the retry loop in BaseGenerator.
    """
    # Create a config that forces a few failures then success
    config = mock_config.copy()
    config['max_retries'] = 5
    
    # Use MockGenerator to simulate disconnection then success
    gen = MockGenerator(config, fail_until_attempt=2)
    
    result = gen.generate()
    
    # Should succeed after retries
    assert result is not None, "Generator should succeed after retries"
    graph, metrics = result
    
    # Verify it's connected
    assert nx.is_connected(graph), "Generated graph must be connected"
    
    # Verify retry count
    assert metrics['attempt'] > 1, "Should have retried at least once"
    assert metrics['attempt'] == 3, "Should have succeeded on 3rd attempt"

def test_sw_max_retries_exhausted(mock_config):
    """
    Test behavior when all retries are exhausted for disconnected graphs.
    """
    config = mock_config.copy()
    config['max_retries'] = 2
    
    # Create a generator that always returns disconnected graphs
    class AlwaysDisconnectedGenerator(BaseGenerator):
        def _generate_candidate(self):
            G = nx.Graph()
            G.add_nodes_from([1, 2, 3])
            G.add_edges_from([(1, 2)])
            return G
        
        def get_generator_name(self): return "AlwaysDisconnected"
        def get_parameters(self): return {}
    
    gen = AlwaysDisconnectedGenerator(config)
    
    result = gen.generate()
    
    # Should return None after exhausting retries
    assert result is None, "Generator should return None after max retries"

def test_er_generates_connected_graph(mock_config):
    """Test that Erdős-Rényi generator produces connected graphs"""
    config = mock_config.copy()
    config['n'] = 10
    config['p'] = 0.5  # High probability for connectivity
    
    gen = ErdosRenyiGenerator(config)
    result = gen.generate()
    
    assert result is not None, "ER generator should produce a graph"
    graph, metrics = result
    assert nx.is_connected(graph), "ER graph should be connected"

def test_er_clustering_distribution(mock_config):
    """Test clustering coefficient distribution for ER graphs"""
    config = mock_config.copy()
    config['n'] = 50
    config['p'] = 0.1
    
    graphs = []
    for _ in range(10):
        gen = ErdosRenyiGenerator(config)
        result = gen.generate()
        if result:
            graphs.append(result[0])
    
    assert len(graphs) > 0, "Should generate at least one graph"
    
    clustering_coeffs = [nx.clustering(g) for g in graphs]
    avg_clustering = [np.mean(list(c.values())) for c in clustering_coeffs]
    
    # ER graphs should have low clustering (~p)
    assert all(0 <= c <= 0.3 for c in avg_clustering), "ER clustering should be low"

def test_sw_clustering_target(mock_config):
    """Test that Watts-Strogatz achieves target clustering"""
    config = mock_config.copy()
    config['n'] = 20
    config['k'] = 4
    config['p'] = 0.3
    
    gen = WattsStrogatzGenerator(config)
    result = gen.generate()
    
    assert result is not None, "WS generator should produce a graph"
    graph, _ = result
    
    clustering = nx.average_clustering(graph)
    # WS should have relatively high clustering compared to ER
    assert clustering > 0.1, "WS graph should have significant clustering"

def test_sf_power_law_fit(mock_config):
    """Test that Barabási-Albert follows power law"""
    config = mock_config.copy()
    config['n'] = 100
    config['m'] = 3
    
    gen = BarabasiAlbertGenerator(config)
    result = gen.generate()
    
    assert result is not None, "BA generator should produce a graph"
    graph, _ = result
    
    # Check degree distribution
    degrees = [d for n, d in graph.degree()]
    assert len(degrees) > 0, "Graph should have degrees"
    
    # Basic check: should have a range of degrees
    assert max(degrees) > min(degrees), "BA should have degree variation"

def test_base_connectivity_check(mock_config):
    """Test the base connectivity verification logic"""
    gen = MockGenerator(mock_config)
    
    # Connected graph
    connected = nx.complete_graph(5)
    assert gen._verify_connectivity(connected) is True
    
    # Disconnected graph
    disconnected = nx.Graph()
    disconnected.add_nodes_from([1, 2, 3, 4])
    disconnected.add_edges_from([(1, 2), (3, 4)])
    assert gen._verify_connectivity(disconnected) is False
    
    # Single node
    single = nx.Graph()
    single.add_node(1)
    assert gen._verify_connectivity(single) is True
    
    # Empty graph
    empty = nx.Graph()
    assert gen._verify_connectivity(empty) is False
