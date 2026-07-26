import pytest
import networkx as nx
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure code/src is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.generators.base import BaseGenerator
from code.src.generators.sw import WattsStrogatzGenerator
from code.src.utils.logging import log_run, log_metric, get_run_log
import json

class MockGenerator(BaseGenerator):
    """Mock generator for testing connectivity logic."""
    def __init__(self, return_disconnected=False, return_connected=True):
        super().__init__()
        self.return_disconnected = return_disconnected
        self.return_connected = return_connected
        self.attempt_count = 0

    def _generate_attempt(self, rng):
        self.attempt_count += 1
        if self.return_disconnected and self.attempt_count < 3:
            # Return a disconnected graph
            G = nx.Graph()
            G.add_nodes_from([1, 2, 3, 4])
            G.add_edges_from([(1, 2), (3, 4)]) # Two components
            return G
        else:
            # Return a connected graph
            G = nx.Graph()
            G.add_nodes_from([1, 2, 3, 4])
            G.add_edges_from([(1, 2), (2, 3), (3, 4)])
            return G

    def get_name(self):
        return "MockGenerator"

def test_sw_retries_on_disconnect():
    """
    Test that the Watts-Strogatz generator (and base class) 
    retries generation when a disconnected graph is produced,
    and eventually returns None if max retries are exceeded.
    """
    config = {
        "global_seed": 42,
        "simulation_params": {
            "max_retry_attempts": 3
        }
    }
    
    # Create a generator that forces disconnected graphs for first 5 attempts
    # but connected on 6th (exceeding limit of 3)
    class AlwaysDisconnectedGenerator(BaseGenerator):
        def _generate_attempt(self, rng):
            G = nx.Graph()
            G.add_nodes_from([1, 2, 3])
            G.add_edges_from([(1, 2)]) # Node 3 is isolated
            return G
        
        def get_name(self):
            return "AlwaysDisconnected"

    gen = AlwaysDisconnectedGenerator(config)
    rng = np.random.default_rng(42)
    
    # Should return None after 3 attempts
    result = gen.generate(rng, graph_id="test_1")
    assert result is None, "Generator should return None when max retries exceeded"
    assert gen.attempt_count == 3, "Generator should have attempted 3 times"

    # Now test the case where it succeeds after a few failures
    class EventuallyConnectedGenerator(BaseGenerator):
        def __init__(self, fail_count):
            super().__init__()
            self.fail_count = fail_count
            self.attempt_count = 0

        def _generate_attempt(self, rng):
            self.attempt_count += 1
            if self.attempt_count <= self.fail_count:
                G = nx.Graph()
                G.add_nodes_from([1, 2, 3])
                G.add_edges_from([(1, 2)]) # Disconnected
                return G
            else:
                G = nx.Graph()
                G.add_nodes_from([1, 2, 3])
                G.add_edges_from([(1, 2), (2, 3)]) # Connected
                return G

        def get_name(self):
            return "EventuallyConnected"

    # Should succeed on 2nd attempt (fail_count=1, limit=3)
    gen_success = EventuallyConnectedGenerator(fail_count=1)
    gen_success.set_run_id("test_run_1")
    result = gen_success.generate(rng, graph_id="test_2")
    assert result is not None, "Generator should return a graph after successful retry"
    assert nx.is_connected(result), "Returned graph must be connected"
    assert gen_success.attempt_count == 2, "Generator should have attempted 2 times"

    # Should succeed on 3rd attempt (fail_count=2, limit=3)
    gen_success_2 = EventuallyConnectedGenerator(fail_count=2)
    gen_success_2.set_run_id("test_run_2")
    result = gen_success_2.generate(rng, graph_id="test_3")
    assert result is not None, "Generator should return a graph after 2 failed attempts"
    assert nx.is_connected(result), "Returned graph must be connected"
    assert gen_success_2.attempt_count == 3, "Generator should have attempted 3 times"

    # Should fail on 3rd attempt (fail_count=3, limit=3)
    gen_fail = EventuallyConnectedGenerator(fail_count=3)
    gen_fail.set_run_id("test_run_3")
    result = gen_fail.generate(rng, graph_id="test_4")
    assert result is None, "Generator should return None if it fails exactly at the limit"
    assert gen_fail.attempt_count == 3, "Generator should have attempted 3 times"

def test_er_generates_connected_graph():
    """Test that Erdos-Renyi generator produces connected graphs when p is high enough."""
    # This test assumes the ER implementation in er.py calls super().generate()
    # and respects the connectivity check.
    from code.src.generators.er import ErdosRenyiGenerator
    
    config = {
        "global_seed": 42,
        "simulation_params": {"max_retry_attempts": 10},
        "topology_targets": {"n": 20, "p": 0.5}
    }
    
    gen = ErdosRenyiGenerator(config)
    rng = np.random.default_rng(42)
    
    result = gen.generate(rng, graph_id="er_test")
    assert result is not None, "ER generator should produce a graph"
    assert nx.is_connected(result), "ER generator should produce a connected graph"

def test_sw_clustering_target():
    """Test that Watts-Strogatz generator respects clustering parameters."""
    from code.src.generators.sw import WattsStrogatzGenerator
    
    config = {
        "global_seed": 42,
        "simulation_params": {"max_retry_attempts": 10},
        "topology_targets": {"n": 20, "k": 4, "p": 0.1}
    }
    
    gen = WattsStrogatzGenerator(config)
    rng = np.random.default_rng(42)
    
    result = gen.generate(rng, graph_id="sw_test")
    assert result is not None, "SW generator should produce a graph"
    assert nx.is_connected(result), "SW generator should produce a connected graph"
    
    # Check clustering coefficient is non-trivial (low p means high clustering)
    cc = nx.average_clustering(result)
    assert cc > 0.0, "Clustering coefficient should be positive"