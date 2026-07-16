import pytest
import os
import sys

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

@pytest.fixture
def sample_config():
    from config import SimulationConfig
    return SimulationConfig(N=100, p=0.1, target_degree=4, seed=42)

@pytest.fixture
def sample_graph():
    import networkx as nx
    G = nx.erdos_renyi_graph(100, 0.1, seed=42)
    return G
