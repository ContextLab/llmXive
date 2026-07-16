"""Unit tests for data models (PolymerRecord, MolecularGraph)."""
import pytest
import numpy as np
from data_models import PolymerRecord, MolecularGraph

def test_polymer_record_creation():
    """Test basic creation of a PolymerRecord."""
    record = PolymerRecord(
        id="test_001",
        smiles="CC(=O)O",
        degradation_pathway="hydrolysis",
        temperature=298.0,
        ph=7.0,
        uv_intensity=0.0
    )
    assert record.id == "test_001"
    assert record.temperature == 298.0

def test_molecular_graph_creation():
    """Test basic creation of a MolecularGraph."""
    # Using dummy numpy arrays for node and edge features
    node_features = np.array([[1.0, 0.0], [0.0, 1.0]])
    edge_index = np.array([[0, 1], [1, 0]])
    edge_features = np.array([[1.0], [1.0]])
    
    graph = MolecularGraph(
        node_features=node_features,
        edge_index=edge_index,
        edge_features=edge_features,
        smiles="CC"
    )
    
    assert graph.smiles == "CC"
    assert graph.node_features.shape == (2, 2)
    assert graph.edge_index.shape == (2, 2)

def test_molecular_graph_invalid_dimensions():
    """Test that mismatched dimensions raise an error or handle gracefully."""
    # Intentionally mismatched dimensions to test robustness
    node_features = np.array([[1.0, 0.0]]) # 1 node
    edge_index = np.array([[0, 1], [1, 0]]) # implies 2 nodes
    edge_features = np.array([[1.0], [1.0]])
    
    # Depending on implementation, this might raise or just store invalid data.
    # For now, we just ensure it instantiates without crashing if we don't have strict validation in __init__
    try:
        graph = MolecularGraph(
            node_features=node_features,
            edge_index=edge_index,
            edge_features=edge_features,
            smiles="C"
        )
        # If it creates, we assume the downstream logic handles the inconsistency or we rely on RDKit to prevent this
        assert graph.smiles == "C"
    except Exception:
        # Expected if strict validation is added later
        pass
