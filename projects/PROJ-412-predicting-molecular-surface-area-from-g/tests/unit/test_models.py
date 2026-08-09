"""
Unit tests for the base data models (Molecule, Graph, EvaluationResult).
"""
import numpy as np
import json
import pytest
from code.models.molecule import Molecule
from code.models.graph import Graph
from code.models.evaluation_result import EvaluationResult


class TestMolecule:
    def test_molecule_creation(self):
        """Test basic molecule creation."""
        mol = Molecule(smiles="CCO", mol_id="test_001")
        assert mol.smiles == "CCO"
        assert mol.mol_id == "test_001"
        assert mol.atom_count == 0
        assert mol.molecular_weight is None

    def test_molecule_with_features(self):
        """Test molecule with node and edge features."""
        node_features = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        edge_features = np.array([[1, 0], [0, 1]])
        
        mol = Molecule(
            smiles="CCO",
            atom_count=3,
            node_features=node_features,
            edge_features=edge_features,
            molecular_weight=46.07
        )
        
        assert mol.atom_count == 3
        assert np.array_equal(mol.node_features, node_features)
        assert np.array_equal(mol.edge_features, edge_features)
        assert mol.molecular_weight == 46.07

    def test_molecule_to_dict(self):
        """Test serialization to dictionary."""
        mol = Molecule(smiles="CCO", atom_count=3, molecular_weight=46.07)
        data = mol.to_dict()
        
        assert data["smiles"] == "CCO"
        assert data["atom_count"] == 3
        assert data["molecular_weight"] == 46.07

    def test_molecule_to_dict_with_arrays(self):
        """Test serialization with numpy arrays."""
        node_features = np.array([[1, 0], [0, 1]])
        mol = Molecule(smiles="CCO", node_features=node_features)
        data = mol.to_dict()
        
        assert isinstance(data["node_features"], list)
        assert data["node_features"] == [[1, 0], [0, 1]]

    def test_molecule_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "smiles": "CCO",
            "mol_id": "test_001",
            "atom_count": 3,
            "molecular_weight": 46.07,
            "node_features": [[1, 0], [0, 1]],
            "edge_features": [[1]],
            "metadata": {"source": "test"}
        }
        
        mol = Molecule.from_dict(data)
        
        assert mol.smiles == "CCO"
        assert mol.mol_id == "test_001"
        assert mol.atom_count == 3
        assert mol.molecular_weight == 46.07
        assert np.array_equal(mol.node_features, np.array([[1, 0], [0, 1]]))
        assert np.array_equal(mol.edge_features, np.array([[1]]))

    def test_molecule_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        mol = Molecule(smiles="CCO", atom_count=3, molecular_weight=46.07)
        json_str = mol.to_json()
        mol_restored = Molecule.from_json(json_str)
        
        assert mol_restored.smiles == mol.smiles
        assert mol_restored.atom_count == mol.atom_count
        assert mol_restored.molecular_weight == mol.molecular_weight


class TestGraph:
    def test_graph_creation(self):
        """Test basic graph creation."""
        graph = Graph(mol_id="test_001")
        assert graph.mol_id == "test_001"
        assert graph.num_nodes == 0
        assert graph.num_edges == 0

    def test_graph_with_features(self):
        """Test graph with node and edge features."""
        x = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
        edge_index = np.array([[0, 1, 1, 2], [1, 0, 2, 1]])
        edge_attr = np.array([[1], [1], [1], [1]])
        
        graph = Graph(
            mol_id="test_001",
            x=x,
            edge_index=edge_index,
            edge_attr=edge_attr,
            y=10.5
        )
        
        assert graph.num_nodes == 3
        assert graph.num_edges == 4
        assert np.array_equal(graph.x, x)
        assert np.array_equal(graph.edge_index, edge_index)
        assert graph.y == 10.5

    def test_graph_to_dict(self):
        """Test serialization to dictionary."""
        graph = Graph(mol_id="test_001", num_nodes=3, num_edges=4, y=10.5)
        data = graph.to_dict()
        
        assert data["mol_id"] == "test_001"
        assert data["num_nodes"] == 3
        assert data["y"] == 10.5

    def test_graph_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "mol_id": "test_001",
            "num_nodes": 2,
            "num_edges": 1,
            "y": 5.0,
            "x": [[1, 0], [0, 1]],
            "edge_index": [[0], [1]],
            "edge_attr": [[1]]
        }
        
        graph = Graph.from_dict(data)
        
        assert graph.mol_id == "test_001"
        assert graph.num_nodes == 2
        assert graph.y == 5.0
        assert np.array_equal(graph.x, np.array([[1, 0], [0, 1]]))


class TestEvaluationResult:
    def test_evaluation_result_creation(self):
        """Test basic evaluation result creation."""
        result = EvaluationResult(
            model_name="GCN",
            dataset_name="ZINC15_subset"
        )
        
        assert result.model_name == "GCN"
        assert result.dataset_name == "ZINC15_subset"
        assert result.mae is None

    def test_evaluation_result_with_metrics(self):
        """Test evaluation result with metrics."""
        result = EvaluationResult(
            model_name="GCN",
            dataset_name="ZINC15_subset",
            mae=0.5,
            rmse=0.8,
            r2=0.92
        )
        
        assert result.mae == 0.5
        assert result.rmse == 0.8
        assert result.r2 == 0.92

    def test_evaluation_result_with_arrays(self):
        """Test evaluation result with prediction arrays."""
        predictions = np.array([1.0, 2.0, 3.0])
        targets = np.array([1.1, 2.2, 2.9])
        
        result = EvaluationResult(
            model_name="GCN",
            dataset_name="ZINC15_subset",
            predictions=predictions,
            targets=targets
        )
        
        assert result.mae is None  # Not calculated automatically in __post_init__
        assert np.array_equal(result.errors, predictions - targets)

    def test_evaluation_result_to_dict(self):
        """Test serialization to dictionary."""
        result = EvaluationResult(
            model_name="GCN",
            dataset_name="ZINC15_subset",
            mae=0.5,
            metadata={"epoch": 10}
        )
        data = result.to_dict()
        
        assert data["model_name"] == "GCN"
        assert data["mae"] == 0.5
        assert data["metadata"]["epoch"] == 10

    def test_evaluation_result_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "model_name": "GCN",
            "dataset_name": "ZINC15_subset",
            "mae": 0.5,
            "rmse": 0.8,
            "r2": 0.92,
            "predictions": [1.0, 2.0, 3.0],
            "targets": [1.1, 2.2, 2.9],
            "metadata": {"seed": 42}
        }
        
        result = EvaluationResult.from_dict(data)
        
        assert result.model_name == "GCN"
        assert result.mae == 0.5
        assert np.array_equal(result.predictions, np.array([1.0, 2.0, 3.0]))
        assert result.metadata["seed"] == 42

    def test_evaluation_result_json_roundtrip(self):
        """Test JSON serialization and deserialization."""
        result = EvaluationResult(
            model_name="GCN",
            dataset_name="ZINC15_subset",
            mae=0.5,
            rmse=0.8,
            r2=0.92
        )
        json_str = result.to_json()
        result_restored = EvaluationResult.from_json(json_str)
        
        assert result_restored.model_name == result.model_name
        assert result_restored.mae == result.mae
        assert result_restored.r2 == result.r2