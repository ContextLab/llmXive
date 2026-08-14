"""
Tests for data ingestion and graph construction.
"""
import pytest
from code.ingest import SyntheticDataGenerator, DefectGraphBuilder
from code.utils import DataAvailabilityError

def test_synthetic_generator():
    gen = SyntheticDataGenerator()
    snaps = gen.generate(2, 100, ["Cu", "Ni"])
    assert len(snaps) == 2
    assert all(s.thermal_conductivity_W_m_K is not None for s in snaps)

def test_defect_graph_builder(sample_snapshot):
    builder = DefectGraphBuilder()
    graph = builder.build(sample_snapshot)
    assert graph.node_count == sample_snapshot.n_atoms
    assert graph.edge_count >= 0
