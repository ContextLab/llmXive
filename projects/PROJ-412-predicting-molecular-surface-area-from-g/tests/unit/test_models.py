"""
Unit tests for base data models: Molecule, Graph, EvaluationResult.
"""
import numpy as np
import pytest
import json

from code.models.molecule import Molecule
from code.models.graph import Graph
from code.models.evaluation_result import EvaluationResult

class TestMolecule:
    def test_molecule_creation(self):
        """Test basic molecule creation."""
        mol = Molecule(
            smiles="CCO",
            molecular_weight=46.07,
            surface_area=60.5
        )
        assert mol.smiles == "CCO"
        assert mol.molecular_weight == 46.07
        assert mol.surface_area == 60.5
        assert mol.conformer_3d is None
        assert mol.metadata == {}

    def test_molecule_with_conformer(self):
        """Test molecule with 3D conformer."""
        coords = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        mol = Molecule(
            smiles="CCO",
            molecular_weight=46.07,
            conformer_3d=coords
        )
        assert mol.conformer_3d.shape == (3, 3)
        np.testing.assert_array_equal(mol.conformer_3d, coords)

    def test_molecule_serialization(self):
        """Test molecule to_dict and from_dict roundtrip."""
        mol = Molecule(
            smiles="CCO",
            molecular_weight=46.07,
            surface_area=60.5,
            metadata={"source": "test"}
        )
        data = mol.to_dict()
        mol_restored = Molecule.from_dict(data)
        assert mol_restored.smiles == mol.smiles
        assert mol_restored.molecular_weight == mol.molecular_weight
        assert mol_restored.surface_area == mol.surface_area
        assert mol_restored.metadata == mol.metadata

    def test_molecule_json(self):
        """Test molecule JSON serialization."""
        mol = Molecule(smiles="CCO", molecular_weight=46.07)
        json_str = mol.to_json()
        mol_restored = Molecule.from_json(json_str)
        assert mol_restored.smiles == mol.smiles
        assert mol_restored.molecular_weight == mol.molecular_weight

class TestGraph:
    def test_graph_creation(self):
        """Test basic graph creation."""
        node_features = np.array([[1, 0], [0, 1], [1, 1]])
        edge_index = np.array([[0, 1], [1, 2]])
        graph = Graph(
            node_features=node_features,
            edge_index=edge_index,
            smiles="CCO",
            molecular_weight=46.07
        )
        assert graph.node_features.shape == (3, 2)
        assert graph.edge_index.shape == (2, 2)
        assert graph.smiles == "CCO"

    def test_graph_with_edge_features(self):
        """Test graph with edge features."""
        node_features = np.array([[1, 0], [0, 1]])
        edge_index = np.array([[0, 1]])
        edge_features = np.array([[0.5, 0.3]])
        graph = Graph(
            node_features=node_features,
            edge_index=edge_index,
            edge_features=edge_features
        )
        assert graph.edge_features.shape == (1, 2)

    def test_graph_serialization(self):
        """Test graph to_dict and from_dict roundtrip."""
        node_features = np.array([[1, 0], [0, 1]])
        edge_index = np.array([[0, 1]])
        graph = Graph(
            node_features=node_features,
            edge_index=edge_index,
            smiles="CCO",
            molecular_weight=46.07
        )
        data = graph.to_dict()
        graph_restored = Graph.from_dict(data)
        np.testing.assert_array_equal(graph_restored.node_features, graph.node_features)
        np.testing.assert_array_equal(graph_restored.edge_index, graph.edge_index)

class TestEvaluationResult:
    def test_evaluation_result_creation(self):
        """Test basic evaluation result creation."""
        predictions = np.array([1.0, 2.0, 3.0])
        targets = np.array([1.1, 2.1, 2.9])
        result = EvaluationResult(
            model_name="test_model",
            predictions=predictions,
            targets=targets
        )
        assert result.model_name == "test_model"
        assert result.samples == 3

    def test_evaluation_result_length_mismatch(self):
        """Test that length mismatch raises error."""
        with pytest.raises(ValueError):
            EvaluationResult(
                model_name="test",
                predictions=np.array([1.0, 2.0]),
                targets=np.array([1.0])
            )

    def test_evaluation_result_metrics(self):
        """Test metrics computation."""
        predictions = np.array([1.0, 2.0, 3.0])
        targets = np.array([1.0, 2.0, 3.0])  # Perfect predictions
        result = EvaluationResult(
            model_name="test_model",
            predictions=predictions,
            targets=targets
        )
        metrics = result.compute_metrics()
        assert metrics["mae"] == 0.0
        assert metrics["rmse"] == 0.0
        assert metrics["r2"] == 1.0

    def test_evaluation_result_serialization(self):
        """Test evaluation result serialization."""
        predictions = np.array([1.0, 2.0])
        targets = np.array([1.0, 2.0])
        result = EvaluationResult(
            model_name="test",
            predictions=predictions,
            targets=targets
        )
        data = result.to_dict()
        result_restored = EvaluationResult.from_dict(data)
        assert result_restored.model_name == result.model_name
        np.testing.assert_array_equal(result_restored.predictions, result.predictions)
        np.testing.assert_array_equal(result_restored.targets, result.targets)