"""
Unit tests for the data models (Molecule, Graph, EvaluationResult).
"""
import numpy as np
import pytest
from code.models import Molecule, Graph, EvaluationResult


class TestMolecule:
    def test_molecule_creation(self):
        """Test basic creation of a Molecule instance."""
        smiles = "CCO"
        mw = 46.07
        node_feats = np.array([[1, 2], [3, 4], [5, 6]])
        edge_idx = np.array([[0, 1], [1, 2]])
        edge_feats = np.array([[1], [1]])

        mol = Molecule(
            smiles=smiles,
            molecular_weight=mw,
            node_features=node_feats,
            edge_index=edge_idx,
            edge_features=edge_feats,
            sasa=20.5
        )

        assert mol.smiles == smiles
        assert mol.molecular_weight == mw
        assert mol.sasa == 20.5
        assert np.array_equal(mol.node_features, node_feats)

    def test_molecule_serialization(self):
        """Test JSON serialization and deserialization."""
        mol = Molecule(
            smiles="C",
            molecular_weight=12.01,
            node_features=np.array([[1]]),
            edge_index=np.array([[0], [0]]),
            edge_features=np.array([[1]]),
            sasa=10.0
        )

        json_str = mol.to_json()
        restored = Molecule.from_json(json_str)

        assert restored.smiles == mol.smiles
        assert restored.molecular_weight == mol.molecular_weight
        assert np.array_equal(restored.node_features, mol.node_features)
        assert restored.sasa == mol.sasa


class TestGraph:
    def test_graph_creation(self):
        """Test basic creation of a Graph instance."""
        node_feats = np.array([[1.0, 0.0], [0.0, 1.0]])
        edge_idx = np.array([[0, 1], [1, 0]])
        edge_feats = np.array([[1.0], [1.0]])

        g = Graph(
            node_features=node_feats,
            edge_index=edge_idx,
            edge_features=edge_feats,
            y=5.5
        )

        assert g.y == 5.5
        assert np.array_equal(g.node_features, node_feats)

    def test_graph_serialization(self):
        """Test JSON serialization and deserialization."""
        g = Graph(
            node_features=np.array([[1.0]]),
            edge_index=np.array([[0], [0]]),
            edge_features=np.array([[1.0]]),
            y=10.0
        )

        json_str = g.to_json()
        restored = Graph.from_json(json_str)

        assert restored.y == g.y
        assert np.array_equal(restored.node_features, g.node_features)


class TestEvaluationResult:
    def test_result_creation(self):
        """Test basic creation of an EvaluationResult instance."""
        preds = np.array([1.0, 2.0, 3.0])
        targets = np.array([1.1, 2.1, 2.9])

        res = EvaluationResult(
            model_name="test_model",
            dataset_name="test_set",
            predictions=preds,
            targets=targets
        )

        res.add_metric("mae", 0.1)

        assert res.model_name == "test_model"
        assert res.get_metric("mae") == 0.1
        assert len(res.predictions) == 3

    def test_result_serialization(self):
        """Test JSON serialization and deserialization."""
        res = EvaluationResult(
            model_name="gcn",
            dataset_name="zinc_test",
            metrics={"mae": 0.5, "rmse": 0.7},
            predictions=np.array([1.0]),
            targets=np.array([1.1])
        )

        json_str = res.to_json()
        restored = EvaluationResult.from_json(json_str)

        assert restored.model_name == res.model_name
        assert restored.get_metric("mae") == 0.5
        assert np.array_equal(restored.predictions, res.predictions)