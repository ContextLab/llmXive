"""
Unit tests for the data models (Molecule, Graph, EvaluationResult).
"""
import pytest
import numpy as np
from code.models.molecule import Molecule
from code.models.graph import Graph
from code.models.evaluation import EvaluationResult

def test_molecule_creation():
    """Test basic Molecule instantiation and serialization."""
    mol = Molecule(
        smiles="CCO",
        molecule_id="mol_001",
        name="Ethanol",
        molecular_weight=46.07,
        sas=50.5
    )
    assert mol.smiles == "CCO"
    assert mol.molecule_id == "mol_001"
    assert mol.name == "Ethanol"
    assert mol.sas == 50.5

    # Test serialization
    data = mol.to_dict()
    assert data["smiles"] == "CCO"
    assert data["molecular_weight"] == 46.07

    json_str = mol.to_json()
    assert "CCO" in json_str

    # Test deserialization
    mol_restored = Molecule.from_dict(data)
    assert mol_restored.smiles == mol.smiles
    assert mol_restored.sas == mol.sas

def test_molecule_defaults():
    """Test default values for optional fields."""
    mol = Molecule(smiles="C", molecule_id="mol_002")
    assert mol.name is None
    assert mol.molecular_weight is None
    assert mol.source == "zinc15"
    assert mol.errors == []

def test_graph_creation():
    """Test Graph instantiation and dimension handling."""
    node_features = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    edge_index = np.array([[0, 1, 1, 2], [1, 0, 2, 1]])

    graph = Graph(
        molecule_id="mol_001",
        node_features=node_features,
        edge_index=edge_index,
        y=10.5
    )

    assert graph.num_nodes == 3
    assert graph.num_edges == 4
    assert graph.y == 10.5

    # Test serialization
    data = graph.to_dict()
    assert isinstance(data["node_features"], list)
    assert isinstance(data["edge_index"], list)
    assert data["y"] == 10.5

    # Test deserialization
    graph_restored = Graph.from_dict(data)
    assert np.array_equal(graph_restored.node_features, node_features)
    assert np.array_equal(graph_restored.edge_index, edge_index)

def test_graph_empty():
    """Test Graph with minimal data."""
    graph = Graph(molecule_id="mol_empty")
    assert graph.num_nodes == 0
    assert graph.num_edges == 0
    assert graph.y is None

def test_evaluation_result_creation():
    """Test EvaluationResult instantiation and metrics."""
    preds = np.array([1.0, 2.0, 3.0])
    targets = np.array([1.1, 2.1, 3.1])

    result = EvaluationResult(
        model_name="gcn_v1",
        dataset_split="test",
        mae=0.1,
        rmse=0.12,
        r2=0.99,
        predictions=preds,
        targets=targets,
        molecule_ids=["m1", "m2", "m3"]
    )

    assert result.model_name == "gcn_v1"
    assert result.mae == 0.1
    assert len(result.predictions) == 3

    # Test serialization
    data = result.to_dict()
    assert data["mae"] == 0.1
    assert "predictions" in data

    # Test deserialization
    result_restored = EvaluationResult.from_dict(data)
    assert result_restored.mae == result.mae
    assert np.array_equal(result_restored.predictions, preds)
