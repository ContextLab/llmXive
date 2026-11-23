"""
Unit tests for data models.
"""
import pytest
import numpy as np
from data_models import PolymerRecord, MolecularGraph

def test_polymer_record_creation():
    """Test basic PolymerRecord creation."""
    record = PolymerRecord(
        polymer_id="P001",
        smiles="CC(=O)OC",
        degradation_pathway="hydrolysis",
        temperature=25.0,
        ph=7.0
    )
    
    assert record.polymer_id == "P001"
    assert record.smiles == "CC(=O)OC"
    assert record.degradation_pathway == "hydrolysis"
    assert record.temperature == 25.0
    assert record.ph == 7.0

def test_molecular_graph_creation():
    """Test basic MolecularGraph creation."""
    graph = MolecularGraph(
        smiles="CC(=O)OC",
        atom_features=np.array([[1, 0], [6, 0], [8, 0]]),
        edge_index=np.array([[0, 1], [1, 2]]),
        edge_type=np.array([0, 0])
    )
    
    assert graph.smiles == "CC(=O)OC"
    assert graph.atom_features.shape[0] == 3
    assert graph.edge_index.shape[1] == 2

def test_polymer_record_missing_optional():
    """Test PolymerRecord with missing optional fields."""
    record = PolymerRecord(
        polymer_id="P002",
        smiles="CCC",
        degradation_pathway=None,
        temperature=None,
        ph=None
    )
    
    assert record.degradation_pathway is None
    assert record.temperature is None
    assert record.ph is None
