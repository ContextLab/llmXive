"""
Unit tests for data models and validation logic.
"""
import pytest
from data_models import PolymerRecord, MolecularGraph

def test_polymer_record_creation(sample_polymer_record_dict):
    """Test that a PolymerRecord can be created from a dictionary."""
    record = PolymerRecord(**sample_polymer_record_dict)
    assert record.smiles == sample_polymer_record_dict["smiles"]
    assert record.degradation_pathway == sample_polymer_record_dict["degradation_pathway"]
    assert record.temperature == sample_polymer_record_dict["temperature"]

def test_polymer_record_missing_optional_fields():
    """Test that PolymerRecord handles missing optional fields."""
    data = {
        "smiles": "CC(=O)OC",
        "degradation_pathway": "hydrolysis"
    }
    record = PolymerRecord(**data)
    assert record.temperature is None
    assert record.ph is None
    assert record.uv_intensity is None

def test_molecular_graph_creation():
    """Test MolecularGraph initialization."""
    graph = MolecularGraph(
        smiles="CC(=O)OC",
        node_features=[[1.0], [2.0]],
        edge_index=[[0, 1], [1, 0]]
    )
    assert graph.smiles == "CC(=O)OC"
    assert len(graph.node_features) == 2
