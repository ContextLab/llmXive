"""
Unit tests for the data schemas and validation helpers.
"""
import pytest
from src.data.schemas import (
    ReactionRecord,
    FeatureVector,
    ModelResult,
    validate_smiles,
    validate_reaction_record,
    validate_feature_vector,
    validate_model_result
)
from datetime import datetime


class TestReactionRecord:
    def test_creation_valid(self):
        record = ReactionRecord(
            reaction_id="123",
            reactants_smiles="CCO",
            products_smiles="CC(=O)O"
        )
        assert record.reaction_id == "123"
        assert record.is_valid()
        assert record.has_target() is False

    def test_creation_with_target(self):
        record = ReactionRecord(
            reaction_id="123",
            reactants_smiles="CCO",
            products_smiles="CC(=O)O",
            yield_pct=85.5
        )
        assert record.has_target() is True
        assert record.yield_pct == 85.5

    def test_creation_with_errors(self):
        record = ReactionRecord(
            reaction_id="123",
            reactants_smiles="CCO",
            products_smiles="CC(=O)O",
            errors=["Missing reagents"]
        )
        assert not record.is_valid()


class TestFeatureVector:
    def test_to_array(self):
        vec = FeatureVector(
            reaction_id="123",
            features={"mw": 100.5, "atoms": 10}
        )
        arr = vec.to_array()
        assert arr == [100.5, 10.0]
        assert vec.feature_names() == ["mw", "atoms"]

    def test_validation_valid(self):
        vec = FeatureVector(reaction_id="123", features={"x": 1.0})
        assert validate_feature_vector(vec) is True

    def test_validation_empty(self):
        vec = FeatureVector(reaction_id="123", features={})
        assert validate_feature_vector(vec) is False

    def test_validation_nan(self):
        import math
        vec = FeatureVector(reaction_id="123", features={"x": float('nan')})
        assert validate_feature_vector(vec) is False

    def test_validation_inf(self):
        vec = FeatureVector(reaction_id="123", features={"x": float('inf')})
        assert validate_feature_vector(vec) is False


class TestModelResult:
    def test_creation_valid(self):
        result = ModelResult(
            reaction_id="123",
            predicted_value=0.95
        )
        assert result.is_valid()

    def test_creation_with_actual(self):
        result = ModelResult(
            reaction_id="123",
            predicted_value=0.95,
            actual_value=0.90
        )
        assert result.actual_value == 0.90

    def test_creation_with_error(self):
        result = ModelResult(
            reaction_id="123",
            predicted_value=0.0,
            error="Model failed"
        )
        assert not result.is_valid()


class TestValidators:
    def test_validate_smiles_valid(self):
        assert validate_smiles("CCO") is True
        assert validate_smiles("c1ccccc1") is True

    def test_validate_smiles_invalid(self):
        assert validate_smiles("") is False
        assert validate_smiles(None) is False
        # Contains invalid char
        assert validate_smiles("CC@O") is False

    def test_validate_reaction_record_missing_id(self):
        raw = {"reactants": "CCO", "products": "CCO"}
        record = validate_reaction_record(raw)
        assert record.reaction_id == "unknown"
        assert "Missing reaction_id" in record.errors

    def test_validate_reaction_record_missing_smiles(self):
        raw = {"reaction_id": "123"}
        record = validate_reaction_record(raw)
        assert "Missing reactants_smiles" in record.errors
        assert "Missing products_smiles" in record.errors

    def test_validate_reaction_record_invalid_yield(self):
        raw = {
            "reaction_id": "123",
            "reactants": "CCO",
            "products": "CCO",
            "yield": 150.0  # Out of range
        }
        record = validate_reaction_record(raw)
        assert any("Yield out of range" in e for e in record.errors)

    def test_validate_reaction_record_success_flag_string(self):
        raw = {
            "reaction_id": "123",
            "reactants": "CCO",
            "products": "CCO",
            "success": "true"
        }
        record = validate_reaction_record(raw)
        assert record.success_flag is True

    def test_validate_reaction_record_success_flag_int(self):
        raw = {
            "reaction_id": "123",
            "reactants": "CCO",
            "products": "CCO",
            "success": 1
        }
        record = validate_reaction_record(raw)
        assert record.success_flag is True