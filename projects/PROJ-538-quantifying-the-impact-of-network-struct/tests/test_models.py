"""
Unit tests for code/models.py
Verifies Pydantic model validation and structure.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# Ensure imports work from tests/
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import AtomicSnapshot, DefectGraph

def test_atomic_snapshot_creation():
    """Test creating a valid AtomicSnapshot."""
    snapshot = AtomicSnapshot(
        snapshot_id="test-001",
        species=["Cu", "Ni", "Cu"],
        coordinates=np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]),
        thermal_conductivity_W_m_K=120.5
    )
    
    assert snapshot.snapshot_id == "test-001"
    assert len(snapshot.species) == 3
    assert snapshot.thermal_conductivity_W_m_K == 120.5

def test_atomic_snapshot_validation():
    """Test that AtomicSnapshot validates coordinates shape."""
    # Coordinates must be 2D (N, 3)
    with pytest.raises(ValueError):
        AtomicSnapshot(
            snapshot_id="test-002",
            species=["Cu", "Ni"],
            coordinates=np.array([0.0, 1.0, 0.0]), # 1D array
            thermal_conductivity_W_m_K=100.0
        )

def test_defect_graph_creation():
    """Test creating a valid DefectGraph."""
    import networkx as nx
    G = nx.Graph()
    G.add_edge(0, 1)
    G.add_edge(1, 2)
    
    graph = DefectGraph(
        snapshot_id="test-001",
        graph_data=G,
        metrics={"clustering": 0.5, "mean_degree": 2.0}
    )
    
    assert graph.snapshot_id == "test-001"
    assert graph.metrics["clustering"] == 0.5
    assert len(graph.graph_data.edges()) == 2
