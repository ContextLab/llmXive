"""
Unit tests for code/models.py
"""
import pytest
import numpy as np
from code.models import AtomicSnapshot, DefectGraph, CorrelationResult
from code.utils import DataAvailabilityError

def test_atomic_snapshot_creation():
    """Test creation of a valid AtomicSnapshot."""
    snapshot = AtomicSnapshot(
        snapshot_id="test_001",
        elements=["Cu", "Ni"],
        species=["Cu", "Ni", "Cu", "Ni"],
        positions=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 0.0]],
        box=[2.0, 2.0, 2.0],
        thermal_conductivity_W_m_K=12.5
    )
    assert snapshot.snapshot_id == "test_001"
    assert len(snapshot.species) == 4
    assert snapshot.thermal_conductivity_W_m_K == 12.5

def test_atomic_snapshot_missing_conductivity():
    """Test that missing thermal conductivity raises DataAvailabilityError."""
    with pytest.raises(DataAvailabilityError):
        AtomicSnapshot(
            snapshot_id="test_002",
            elements=["Au"],
            species=["Au"],
            positions=[[0.0, 0.0, 0.0]],
            box=[1.0, 1.0, 1.0]
            # thermal_conductivity_W_m_K is missing
        )

def test_defect_graph_creation():
    """Test creation of a DefectGraph."""
    graph = DefectGraph(
        snapshot_id="test_001",
        nodes=[{"id": 0, "species": "Cu"}, {"id": 1, "species": "Ni"}],
        edges=[{"source": 0, "target": 1, "type": "mismatch"}],
        metrics={"clustering": 0.5, "mean_degree": 1.0}
    )
    assert graph.snapshot_id == "test_001"
    assert len(graph.edges) == 1

def test_correlation_result():
    """Test CorrelationResult model."""
    result = CorrelationResult(
        metric_name="clustering",
        target="thermal_conductivity",
        method="pearson",
        coefficient=0.85,
        p_value=0.001,
        corrected_p_value=0.005
    )
    assert result.coefficient == 0.85
