import pytest
from preprocess import (
    validate_smiles,
    smiles_to_molecular_graph,
    filter_missing_environmental_data,
    filter_polyesters
)
from data_models import MolecularGraph


class TestValidateSmiles:
    def test_valid_smiles(self):
        assert validate_smiles("CCO") is True
        assert validate_smiles("c1ccccc1") is True

    def test_invalid_smiles(self):
        assert validate_smiles("invalid") is False
        assert validate_smiles("") is False
        assert validate_smiles(None) is False


class TestSmilesToMolecularGraph:
    def test_conversion_success(self):
        graph = smiles_to_molecular_graph("CCO", "test_id")
        assert graph is not None
        assert graph.record_id == "test_id"
        assert graph.num_atoms > 0

    def test_conversion_failure(self):
        graph = smiles_to_molecular_graph("invalid_smiles_xyz", "test_id")
        assert graph is None


class TestFilterMissingEnvironmentalData:
    def test_all_valid(self):
        records = [
            {"id": "1", "temperature": 25.0, "ph": 7.0, "uv_intensity": 10.0},
            {"id": "2", "temperature": 30.0, "ph": 6.5, "uv_intensity": 5.0},
        ]
        result = filter_missing_environmental_data(records)
        assert len(result) == 2

    def test_missing_ph_excludes(self):
        records = [
            {"id": "1", "temperature": 25.0, "ph": 7.0, "uv_intensity": 10.0},
            {"id": "2", "temperature": 30.0, "ph": None, "uv_intensity": 5.0},
        ]
        result = filter_missing_environmental_data(records)
        assert len(result) == 1
        assert result[0]["id"] == "1"

    def test_missing_temp_excludes(self):
        records = [
            {"id": "1", "temperature": None, "ph": 7.0, "uv_intensity": 10.0},
        ]
        result = filter_missing_environmental_data(records)
        assert len(result) == 0

    def test_missing_uv_excludes(self):
        records = [
            {"id": "1", "temperature": 25.0, "ph": 7.0, "uv_intensity": None},
        ]
        result = filter_missing_environmental_data(records)
        assert len(result) == 0


class TestFilterPolyesters:
    def test_polyester_detected(self):
        # Ethyl acetate: CC(=O)OCC
        records = [
            {"id": "1", "smiles": "CC(=O)OCC"},
        ]
        result = filter_polyesters(records)
        assert len(result) == 1

    def test_non_polyester_excluded(self):
        # Hexane: CCCCCC
        records = [
            {"id": "1", "smiles": "CCCCCC"},
        ]
        result = filter_polyesters(records)
        assert len(result) == 0

    def test_mixed_records(self):
        records = [
            {"id": "1", "smiles": "CC(=O)OCC"}, # Polyester
            {"id": "2", "smiles": "CCCCCC"},    # Non-polyester
            {"id": "3", "smiles": "CC(=O)OC"},  # Polyester
        ]
        result = filter_polyesters(records)
        assert len(result) == 2
        ids = [r["id"] for r in result]
        assert "1" in ids
        assert "3" in ids
        assert "2" not in ids
