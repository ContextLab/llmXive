"""
Unit tests for the data models (Molecule, Graph, EvaluationResult).
"""
import numpy as np
import pytest
from code.models.molecule import Molecule
from code.models.graph import Graph
from code.models.evaluation_result import EvaluationResult


class TestMolecule:
    def test_molecule_creation(self):
        """Test basic molecule creation."""
        mol = Molecule(smiles="CCO", molecule_id="test_001")
        assert mol.smiles == "CCO"
        assert mol.molecule_id == "test_001"
        assert mol.metadata == {}

    def test_molecule_with_metadata(self):
        """Test molecule creation with metadata."""
        metadata = {"source": "zinc15", "processed": True}
        mol = Molecule(smiles="CCO", metadata=metadata)
        assert mol.metadata == metadata

    def test_molecule_to_dict(self):
        """Test molecule serialization to dict."""
        mol = Molecule(smiles="CCO", molecule_id="test_001", metadata={"key": "value"})
        d = mol.to_dict()
        assert d["smiles"] == "CCO"
        assert d["molecule_id"] == "test_001"
        assert d["metadata"]["key"] == "value"

    def test_molecule_roundtrip(self):
        """Test JSON roundtrip for molecule."""
        original = Molecule(smiles="CCO", molecule_id="test_001", metadata={"key": "value"})
        json_str = original.to_json()
        restored = Molecule.from_json(json_str)
        assert restored.smiles == original.smiles
        assert restored.molecule_id == original.molecule_id
        assert restored.metadata == original.metadata


class TestGraph:
    def test_graph_creation(self):
        """Test basic graph creation."""
        node_features = np.array([[1.0, 0.0], [0.0, 1.0]])
        edge_index = np.array([[0, 1], [1, 0]])
        g = Graph(node_features=node_features, edge_index=edge_index)
        assert g.node_features.shape == (2, 2)
        assert g.edge_index.shape == (2, 2)
        assert g.edge_features is None

    def test_graph_with_features(self):
        """Test graph creation with edge features."""
        node_features = np.array([[1.0, 0.0]])
        edge_index = np.array([[0, 0]])
        edge_features = np.array([[0.5]])
        g = Graph(
            node_features=node_features,
            edge_index=edge_index,
            edge_features=edge_features,
            molecular_weight=46.07,
            surface_area=50.5
        )
        assert g.molecular_weight == 46.07
        assert g.surface_area == 50.5
        assert np.array_equal(g.edge_features, edge_features)

    def test_graph_to_dict(self):
        """Test graph serialization to dict."""
        g = Graph(
            node_features=np.array([[1.0]]),
            edge_index=np.array([[0], [0]]),
            edge_features=np.array([[0.5]]),
            molecular_weight=46.0,
            surface_area=50.0,
            metadata={"source": "test"}
        )
        d = g.to_dict()
        assert d["molecular_weight"] == 46.0
        assert d["surface_area"] == 50.0
        assert d["metadata"]["source"] == "test"

    def test_graph_roundtrip(self):
        """Test dictionary roundtrip for graph."""
        original = Graph(
            node_features=np.array([[1.0, 0.0], [0.0, 1.0]]),
            edge_index=np.array([[0, 1], [1, 0]]),
            edge_features=np.array([[0.5]]),
            molecular_weight=46.07,
            surface_area=50.5,
            metadata={"key": "value"}
        )
        d = original.to_dict()
        restored = Graph.from_dict(d)
        assert np.array_equal(restored.node_features, original.node_features)
        assert np.array_equal(restored.edge_index, original.edge_index)
        assert np.array_equal(restored.edge_features, original.edge_features)
        assert restored.molecular_weight == original.molecular_weight
        assert restored.surface_area == original.surface_area


class TestEvaluationResult:
    def test_evaluation_result_creation(self):
        """Test basic evaluation result creation."""
        result = EvaluationResult(
            model_name="GCN",
            mae=0.5,
            rmse=0.7,
            r2=0.9
        )
        assert result.model_name == "GCN"
        assert result.mae == 0.5
        assert result.rmse == 0.7
        assert result.r2 == 0.9

    def test_evaluation_result_with_data(self):
        """Test evaluation result with predictions and targets."""
        result = EvaluationResult(
            model_name="GCN",
            mae=0.5,
            rmse=0.7,
            r2=0.9,
            predictions=[1.0, 2.0, 3.0],
            targets=[1.1, 2.1, 2.9],
            metrics={"mae_per_class": {"class1": 0.4}}
        )
        assert len(result.predictions) == 3
        assert len(result.targets) == 3
        assert result.metrics["mae_per_class"]["class1"] == 0.4

    def test_evaluation_result_to_dict(self):
        """Test evaluation result serialization to dict."""
        result = EvaluationResult(
            model_name="GCN",
            mae=0.5,
            rmse=0.7,
            r2=0.9,
            predictions=[1.0],
            targets=[1.1],
            metrics={"key": "value"}
        )
        d = result.to_dict()
        assert d["model_name"] == "GCN"
        assert d["predictions"] == [1.0]
        assert d["metrics"]["key"] == "value"

    def test_evaluation_result_roundtrip(self):
        """Test JSON roundtrip for evaluation result."""
        original = EvaluationResult(
            model_name="GCN",
            mae=0.5,
            rmse=0.7,
            r2=0.9,
            predictions=[1.0, 2.0],
            targets=[1.1, 2.1],
            metrics={"key": "value"}
        )
        json_str = original.to_json()
        restored = EvaluationResult.from_json(json_str)
        assert restored.model_name == original.model_name
        assert restored.mae == original.mae
        assert restored.predictions == original.predictions
        assert restored.metrics == original.metrics
