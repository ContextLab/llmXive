"""
Unit tests for preprocessing logic.
"""
import pytest
from preprocess import canonicalize_smiles, smiles_to_molecular_graph, filter_missing_environmental_data

def test_smiles_canonicalization():
    """Test SMILES canonicalization."""
    # Different representations of the same molecule
    smiles1 = "CCO"
    smiles2 = "OCC"
    
    canon1 = canonicalize_smiles(smiles1)
    canon2 = canonicalize_smiles(smiles2)
    
    assert canon1 == canon2
    assert canon1 == "CCO"

def test_missing_env_excludes_record():
    """Test that records with missing environmental data are excluded."""
    records = [
        {"id": "1", "temperature": 25.0, "ph": 7.0, "uv": 10.0},
        {"id": "2", "temperature": None, "ph": 7.0, "uv": 10.0},
        {"id": "3", "temperature": 25.0, "ph": None, "uv": 10.0},
        {"id": "4", "temperature": 25.0, "ph": 7.0, "uv": None},
        {"id": "5", "temperature": 25.0, "ph": 7.0, "uv": 10.0},
    ]
    
    filtered, flagged = filter_missing_environmental_data(records)
    
    assert len(filtered) == 2  # Records 1 and 5
    assert len(flagged) == 3  # Records 2, 3, and 4
    assert [r["id"] for r in flagged] == ["2", "3", "4"]

def test_smiles_to_molecular_graph():
    """Test conversion of SMILES to molecular graph."""
    graph = smiles_to_molecular_graph("CC(=O)OC")
    assert graph is not None
    assert "atom_features" in graph
    assert "edge_index" in graph
    assert graph["valid"] is True