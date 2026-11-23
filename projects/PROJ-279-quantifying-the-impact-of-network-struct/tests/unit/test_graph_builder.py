import pytest
import networkx as nx
import numpy as np
from pathlib import Path
import logging

# Adjust imports based on project structure
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from graph_builder import build_graph_from_atoms, validate_graph_connectivity
from models.atomic_config import AtomicConfiguration

@pytest.fixture
def sample_config_connected():
    """
    Create a simple connected structure: 4 atoms in a line.
    Positions: (0,0,0), (1,0,0), (2,0,0), (3,0,0)
    Cutoff: 1.5 -> edges (0-1), (1-2), (2-3)
    """
    positions = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        [3.0, 0.0, 0.0]
    ])
    return AtomicConfiguration(
        id="test_connected",
        positions=positions,
        numbers=[14, 14, 14, 14], # Si
        cell=[10, 10, 10],
        pbc=[False, False, False]
    )

@pytest.fixture
def sample_config_disconnected():
    """
    Create a disconnected structure: 2 pairs far apart.
    Positions: (0,0,0), (1,0,0) and (10,0,0), (11,0,0)
    Cutoff: 1.5 -> edges (0-1), (2-3). Two components.
    """
    positions = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [10.0, 0.0, 0.0],
        [11.0, 0.0, 0.0]
    ])
    return AtomicConfiguration(
        id="test_disconnected",
        positions=positions,
        numbers=[14, 14, 14, 14],
        cell=[20, 20, 20],
        pbc=[False, False, False]
    )

@pytest.fixture
def caplog(caplog):
    caplog.set_level(logging.WARNING)
    return caplog

def test_build_graph_connected(sample_config_connected):
    graph = build_graph_from_atoms(sample_config_connected, cutoff_radius=1.5)
    assert graph.number_of_nodes() == 4
    assert graph.number_of_edges() == 3
    assert nx.is_connected(graph)

def test_build_graph_disconnected(sample_config_disconnected):
    graph = build_graph_from_atoms(sample_config_disconnected, cutoff_radius=1.5)
    assert graph.number_of_nodes() == 4
    assert graph.number_of_edges() == 2
    assert not nx.is_connected(graph)
    assert nx.number_connected_components(graph) == 2

def test_validate_graph_connectivity_connected(sample_config_connected, caplog):
    graph = build_graph_from_atoms(sample_config_connected, cutoff_radius=1.5)
    is_connected, disconnected_sizes = validate_graph_connectivity(graph, "test_connected")
    
    assert is_connected is True
    assert disconnected_sizes == []
    # Check that no warning was logged
    assert "Disconnected components" not in caplog.text

def test_validate_graph_connectivity_disconnected(sample_config_disconnected, caplog):
    graph = build_graph_from_atoms(sample_config_disconnected, cutoff_radius=1.5)
    is_connected, disconnected_sizes = validate_graph_connectivity(graph, "test_disconnected")
    
    assert is_connected is False
    assert len(disconnected_sizes) == 1
    assert disconnected_sizes[0] == 2 # One component of size 2 (besides the largest)
    
    # Check that a warning was logged (Spec US-1 Scenario 3)
    assert "Disconnected components detected" in caplog.text
    assert "test_disconnected" in caplog.text
    assert "largest component" in caplog.text.lower()

def test_validate_graph_empty():
    empty_config = AtomicConfiguration(
        id="test_empty",
        positions=np.array([]).reshape(0, 3),
        numbers=[],
        cell=[10, 10, 10],
        pbc=[False, False, False]
    )
    graph = build_graph_from_atoms(empty_config, cutoff_radius=1.5)
    is_connected, disconnected_sizes = validate_graph_connectivity(graph, "test_empty")
    
    assert is_connected is False
    assert disconnected_sizes == []
