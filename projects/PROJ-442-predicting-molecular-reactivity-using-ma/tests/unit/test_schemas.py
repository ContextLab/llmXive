"""
Unit tests for data schemas and validation helpers.

Tests cover:
- ReactionRecord validation (SMILES, target variables)
- FeatureVector validation
- ModelResult validation
- Helper function correctness
"""
import pytest
from datetime import datetime
from src.data.schemas import (
    ReactionRecord,
    FeatureVector,
    ModelResult,
    validate_reaction_type,
    validate_yield_range,
    validate_smiles_list,
    _is_valid_smiles
)


class TestReactionRecord:
    """Tests for ReactionRecord schema validation."""

    def test_valid_reaction_record(self):
        """Test creation of a valid ReactionRecord."""
        record = ReactionRecord(
            reaction_id="test_001",
            reactants_smiles=["CCO", "CC(=O)O"],
            products_smiles=["CC(=O)OCC"],
            reaction_type="SN2",
            yield_pct=85.5,
            success_flag=1
        )
        assert record.reaction_id == "test_001"
        assert record.reaction_type == "SN2"
        assert record.yield_pct == 85.5

    def test_valid_record_with_only_success_flag(self):
        """Test that success_flag alone is sufficient."""
        record = ReactionRecord(
            reaction_id="test_002",
            reactants_smiles=["CCO"],
            products_smiles=["CC=O"],
            success_flag=1
        )
        assert record.success_flag == 1
        assert record.yield_pct is None

    def test_valid_record_with_only_yield(self):
        """Test that yield_pct alone is sufficient."""
        record = ReactionRecord(
            reaction_id="test_003",
            reactants_smiles=["C"],
            products_smiles=["CO"],
            yield_pct=50.0
        )
        assert record.yield_pct == 50.0

    def test_missing_target_variable_raises_error(self):
        """Test that missing both target variables raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ReactionRecord(
                reaction_id="test_004",
                reactants_smiles=["C"],
                products_smiles=["CO"]
            )
        assert "Either yield_pct or success_flag" in str(exc_info.value)

    def test_invalid_reactant_smiles_raises_error(self):
        """Test that invalid reactant SMILES raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ReactionRecord(
                reaction_id="test_005",
                reactants_smiles=["INVALID_SMILES"],
                products_smiles=["CO"]
            )
        assert "Invalid reactant SMILES" in str(exc_info.value)

    def test_invalid_product_smiles_raises_error(self):
        """Test that invalid product SMILES raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ReactionRecord(
                reaction_id="test_006",
                reactants_smiles=["CCO"],
                products_smiles=["INVALID"]
            )
        assert "Invalid product SMILES" in str(exc_info.value)

    def test_empty_reactants_raises_error(self):
        """Test that empty reactants list raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ReactionRecord(
                reaction_id="test_007",
                reactants_smiles=[],
                products_smiles=["CO"]
            )
        assert "Reactants list cannot be empty" in str(exc_info.value)

    def test_yield_out_of_range_raises_error(self):
        """Test that yield > 100 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ReactionRecord(
                reaction_id="test_008",
                reactants_smiles=["C"],
                products_smiles=["CO"],
                yield_pct=150.0
            )
        assert "greater than 100" in str(exc_info.value) or "less than 0" in str(exc_info.value)

    def test_diels_alder_reaction_type(self):
        """Test Diels-Alder reaction type is accepted."""
        record = ReactionRecord(
            reaction_id="test_009",
            reactants_smiles=["C=CC=C", "C=C"],
            products_smiles=["C1CC=CC1"],
            reaction_type="Diels-Alder",
            yield_pct=75.0
        )
        assert record.reaction_type == "Diels-Alder"


class TestFeatureVector:
    """Tests for FeatureVector schema validation."""

    def test_valid_feature_vector(self):
        """Test creation of a valid FeatureVector."""
        fv = FeatureVector(
            reaction_id="test_001",
            features={"mw": 120.5, "atom_count": 15},
            molecular_weights={"reactants": 80.0, "products": 100.0}
        )
        assert fv.reaction_id == "test_001"
        assert fv.features["mw"] == 120.5

    def test_negative_feature_raises_error(self):
        """Test that negative feature values raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            FeatureVector(
                reaction_id="test_010",
                features={"negative_feature": -5.0}
            )
        assert "non-negative" in str(exc_info.value)


class TestModelResult:
    """Tests for ModelResult schema validation."""

    def test_valid_model_result(self):
        """Test creation of a valid ModelResult."""
        result = ModelResult(
            reaction_id="test_001",
            predicted_value=85.0,
            actual_value=82.5,
            reaction_type="SN2",
            confidence_score=0.92
        )
        assert result.predicted_value == 85.0
        assert result.actual_value == 82.5

    def test_prediction_out_of_range_raises_error(self):
        """Test that prediction > 100 raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ModelResult(
                reaction_id="test_011",
                predicted_value=150.0
            )
        assert "between 0 and 100" in str(exc_info.value)

    def test_result_without_actual_value(self):
        """Test that ModelResult can be created without actual_value."""
        result = ModelResult(
            reaction_id="test_012",
            predicted_value=50.0
        )
        assert result.actual_value is None


class TestValidationHelpers:
    """Tests for standalone validation helper functions."""

    def test_validate_reaction_type_valid(self):
        """Test valid reaction types."""
        assert validate_reaction_type("SN1") is True
        assert validate_reaction_type("SN2") is True
        assert validate_reaction_type("Diels-Alder") is True

    def test_validate_reaction_type_invalid(self):
        """Test invalid reaction types."""
        assert validate_reaction_type("E1") is False
        assert validate_reaction_type("Invalid") is False
        assert validate_reaction_type("") is False

    def test_validate_yield_range_valid(self):
        """Test valid yield ranges."""
        assert validate_yield_range(0.0) is True
        assert validate_yield_range(50.0) is True
        assert validate_yield_range(100.0) is True

    def test_validate_yield_range_invalid(self):
        """Test invalid yield ranges."""
        assert validate_yield_range(-1.0) is False
        assert validate_yield_range(101.0) is False

    def test_validate_smiles_list_valid(self):
        """Test valid SMILES lists."""
        assert validate_smiles_list(["CCO", "CC(=O)O"]) is True
        assert validate_smiles_list(["C"]) is True

    def test_validate_smiles_list_invalid(self):
        """Test invalid SMILES lists."""
        assert validate_smiles_list(["INVALID"]) is False
        assert validate_smiles_list([]) is False

    def test_is_valid_smiles_function(self):
        """Test the internal SMILES validation function."""
        assert _is_valid_smiles("CCO") is True
        assert _is_valid_smiles("C1=CC=C1") is True
        assert _is_valid_smiles("INVALID") is False
        assert _is_valid_smiles("") is False
        assert _is_valid_smiles(None) is False