import pytest
import numpy as np
from code.models.molecule import Molecule
from code.models.graph import Graph
from code.models.evaluation_result import EvaluationResult


class TestMolecule:
    def test_molecule_creation(self):
        mol = Molecule(
            smiles="CCO",
            atom_count=3,
            molecular_weight=46.07
        )
        assert mol.smiles == "CCO"
        assert mol.atom_count == 3
        assert mol.molecular_weight == 46.07

    def test_molecule_with_features(self):
        node_features = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
        mol = Molecule(
            smiles="CCO",
            atom_count=3,
            node_features=node_features
        )
        assert np.array_equal(mol.node_features, node_features)

    def test_molecule_to_dict(self):
        mol = Molecule(
            smiles="CCO",
            atom_count=3,
            molecular_weight=46.07,
            surface_area=50.0
        )
        data = mol.to_dict()
        assert data["smiles"] == "CCO"
        assert data["surface_area"] == 50.0

    def test_molecule_roundtrip(self):
        mol = Molecule(
            smiles="C1=CC=CC=C1",
            atom_count=6,
            molecular_weight=78.11,
            surface_area=100.5
        )
        json_str = mol.to_json()
        mol_restored = Molecule.from_json(json_str)
        assert mol_restored.smiles == mol.smiles
        assert mol_restored.atom_count == mol.atom_count
        assert mol_restored.surface_area == mol.surface_area

    def test_molecule_invalid_atom_count(self):
        with pytest.raises(ValueError):
            Molecule(smiles="C", atom_count=0)


class TestGraph:
    def test_graph_creation(self):
        node_features = np.array([[1.0, 0.0], [0.0, 1.0]])
        edge_features = np.array([[1.0]])
        edge_index = np.array([[0, 1], [1, 0]])
        
        g = Graph(
            smiles="CC",
            num_nodes=2,
            num_edges=2,
            node_features=node_features,
            edge_features=edge_features,
            edge_index=edge_index,
            surface_area=40.0
        )
        assert g.smiles == "CC"
        assert g.num_nodes == 2
        assert g.surface_area == 40.0

    def test_graph_dimension_mismatch(self):
        node_features = np.array([[1.0, 0.0]])
        edge_features = np.array([[1.0]])
        edge_index = np.array([[0, 1], [1, 0]])
        
        with pytest.raises(ValueError):
            Graph(
                smiles="CC",
                num_nodes=2,
                num_edges=2,
                node_features=node_features,
                edge_features=edge_features,
                edge_index=edge_index
            )

    def test_graph_to_dict(self):
        node_features = np.array([[1.0, 0.0], [0.0, 1.0]])
        edge_features = np.array([[1.0]])
        edge_index = np.array([[0, 1], [1, 0]])
        
        g = Graph(
            smiles="CC",
            num_nodes=2,
            num_edges=2,
            node_features=node_features,
            edge_features=edge_features,
            edge_index=edge_index
        )
        data = g.to_dict()
        assert data["num_nodes"] == 2
        assert data["smiles"] == "CC"

    def test_graph_roundtrip(self):
        node_features = np.array([[1.0, 0.0], [0.0, 1.0]])
        edge_features = np.array([[1.0]])
        edge_index = np.array([[0, 1], [1, 0]])
        
        g = Graph(
            smiles="CC",
            num_nodes=2,
            num_edges=2,
            node_features=node_features,
            edge_features=edge_features,
            edge_index=edge_index,
            molecular_weight=30.07
        )
        json_str = g.to_json()
        g_restored = Graph.from_json(json_str)
        assert g_restored.smiles == g.smiles
        assert np.array_equal(g_restored.node_features, g.node_features)


class TestEvaluationResult:
    def test_evaluation_result_creation(self):
        preds = np.array([10.0, 20.0, 30.0])
        targets = np.array([11.0, 19.0, 31.0])
        smiles = ["C", "CC", "CCC"]
        errors = preds - targets
        
        res = EvaluationResult(
            model_type="GCN",
            mae=1.0,
            rmse=1.0,
            r2=0.99,
            predictions=preds,
            targets=targets,
            smiles_list=smiles,
            errors=errors
        )
        
        assert res.model_type == "GCN"
        assert len(res.smiles_list) == 3

    def test_evaluation_result_to_dict(self):
        preds = np.array([10.0])
        targets = np.array([11.0])
        errors = np.array([-1.0])
        
        res = EvaluationResult(
            model_type="Baseline",
            mae=1.0,
            rmse=1.0,
            r2=0.5,
            predictions=preds,
            targets=targets,
            smiles_list=["C"],
            errors=errors
        )
        
        data = res.to_dict()
        assert data["mae"] == 1.0
        assert isinstance(data["predictions"], list)

    def test_evaluation_result_roundtrip(self):
        preds = np.array([10.0, 20.0])
        targets = np.array([11.0, 19.0])
        errors = np.array([-1.0, 1.0])
        
        res = EvaluationResult(
            model_type="GCN",
            mae=1.0,
            rmse=1.0,
            r2=0.9,
            predictions=preds,
            targets=targets,
            smiles_list=["C", "CC"],
            errors=errors,
            hyperparameters={"lr": 0.01}
        )
        
        json_str = res.to_json()
        res_restored = EvaluationResult.from_json(json_str)
        
        assert res_restored.model_type == res.model_type
        assert np.allclose(res_restored.predictions, res.predictions)
        assert res_restored.hyperparameters["lr"] == 0.01

    def test_evaluation_result_summary(self):
        preds = np.array([10.0])
        targets = np.array([11.0])
        errors = np.array([-1.0])
        
        res = EvaluationResult(
            model_type="GCN",
            mae=1.0,
            rmse=1.0,
            r2=0.9,
            predictions=preds,
            targets=targets,
            smiles_list=["C"],
            errors=errors
        )
        
        summary = res.summary()
        assert "GCN" in summary
        assert "MAE" in summary