"""
Contract test for CLMM output schema validation.

This test verifies that the CLMM results produced by code/02_fit_clmm.py
conform to the schema defined in contracts/output.schema.yaml.
"""

import json
import yaml
from pathlib import Path
import pytest

from code.utils.schema_validator import (
    load_schema,
    validate_object,
    SchemaValidationError,
)


def load_output_schema():
    """Load the output schema from contracts/output.schema.yaml."""
    schema_path = Path("contracts/output.schema.yaml")
    if not schema_path.exists():
        pytest.skip(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


def create_valid_sample_result():
    """Create a sample result that should pass validation."""
    return {
        "model_info": {
            "formula": "quality_rating ~ politeness + conversation_length + (1|user_id)",
            "family": "cumulative",
            "convergence_status": True,
            "convergence_message": "Model converged successfully",
            "n_observations": 500,
            "n_groups": 100,
            "link_function": "logit",
        },
        "fixed_effects": [
            {
                "term": "(Intercept)",
                "estimate": -0.5,
                "std_error": 0.15,
                "z_value": -3.33,
                "p_value": 0.0009,
                "p_value_adj": 0.0018,
                "ci_lower": -0.79,
                "ci_upper": -0.21,
                "significance": "***",
            },
            {
                "term": "politeness",
                "estimate": 0.45,
                "std_error": 0.12,
                "z_value": 3.75,
                "p_value": 0.0002,
                "p_value_adj": 0.0004,
                "ci_lower": 0.21,
                "ci_upper": 0.69,
                "significance": "***",
            },
            {
                "term": "conversation_length",
                "estimate": 0.02,
                "std_error": 0.01,
                "z_value": 2.0,
                "p_value": 0.0455,
                "p_value_adj": 0.0683,
                "ci_lower": 0.0004,
                "ci_upper": 0.0396,
                "significance": "*",
            },
        ],
        "random_effects": {
            "user_id": {
                "variance": 0.25,
                "std_dev": 0.5,
                "n_levels": 100,
            }
        },
        "diagnostics": {
            "aic": 1250.5,
            "bic": 1280.3,
            "log_likelihood": -615.25,
            "residual_df": 485,
            "rho": 0.15,
            "n_thresholds": 4,
        },
        "thresholds": [
            {
                "threshold_name": "1|2",
                "estimate": -1.2,
                "std_error": 0.18,
            },
            {
                "threshold_name": "2|3",
                "estimate": 0.3,
                "std_error": 0.15,
            },
            {
                "threshold_name": "3|4",
                "estimate": 1.8,
                "std_error": 0.20,
            },
            {
                "threshold_name": "4|5",
                "estimate": 3.1,
                "std_error": 0.22,
            },
        ],
    }


def create_invalid_result_missing_field():
    """Create a result missing a required field."""
    result = create_valid_sample_result()
    del result["model_info"]["convergence_status"]
    return result


def create_invalid_result_wrong_type():
    """Create a result with wrong data types."""
    result = create_valid_sample_result()
    result["model_info"]["n_observations"] = "five hundred"  # Should be int
    return result


def create_invalid_result_negative_pvalue():
    """Create a result with invalid p-value (negative)."""
    result = create_valid_sample_result()
    result["fixed_effects"][0]["p_value"] = -0.1
    return result


class TestOutputSchema:
    """Tests for CLMM output schema validation."""

    @pytest.fixture
    def schema(self):
        return load_output_schema()

    def test_schema_file_exists(self):
        """Test that the output schema file exists."""
        schema_path = Path("contracts/output.schema.yaml")
        assert schema_path.exists(), "Output schema file must exist"

    def test_valid_result_passes_validation(self, schema):
        """Test that a valid result passes schema validation."""
        result = create_valid_sample_result()
        # This should not raise
        validate_object(result, schema)

    def test_missing_required_field_fails(self, schema):
        """Test that missing required fields cause validation failure."""
        result = create_invalid_result_missing_field()
        with pytest.raises(SchemaValidationError):
            validate_object(result, schema)

    def test_wrong_type_fails(self, schema):
        """Test that wrong data types cause validation failure."""
        result = create_invalid_result_wrong_type()
        with pytest.raises(SchemaValidationError):
            validate_object(result, schema)

    def test_negative_pvalue_fails(self, schema):
        """Test that negative p-values cause validation failure."""
        result = create_invalid_result_negative_pvalue()
        with pytest.raises(SchemaValidationError):
            validate_object(result, schema)

    def test_empty_fixed_effects_fails(self, schema):
        """Test that empty fixed_effects array fails validation."""
        result = create_valid_sample_result()
        result["fixed_effects"] = []
        with pytest.raises(SchemaValidationError):
            validate_object(result, schema)

    def test_missing_thresholds_fails(self, schema):
        """Test that missing thresholds field fails validation."""
        result = create_valid_sample_result()
        del result["thresholds"]
        with pytest.raises(SchemaValidationError):
            validate_object(result, schema)

    def test_schema_structure(self, schema):
        """Test that the schema has the expected top-level structure."""
        required_keys = ["model_info", "fixed_effects", "random_effects", "diagnostics"]
        for key in required_keys:
            assert key in schema.get("required", []), f"Schema must require '{key}'"

    def test_fixed_effects_item_structure(self, schema):
        """Test that fixed_effects items have required structure."""
        fixed_effect_schema = schema["properties"]["fixed_effects"]["items"]
        required_effect_keys = [
            "term",
            "estimate",
            "std_error",
            "z_value",
            "p_value",
            "p_value_adj",
            "ci_lower",
            "ci_upper",
        ]
        for key in required_effect_keys:
            assert key in fixed_effect_schema.get("required", []), \
                f"Fixed effect item must require '{key}'"

    def test_random_effects_structure(self, schema):
        """Test that random_effects has expected structure."""
        random_effects_schema = schema["properties"]["random_effects"]
        assert "user_id" in random_effects_schema.get("required", []), \
            "random_effects must require 'user_id'"

    def test_diagnostics_structure(self, schema):
        """Test that diagnostics has expected structure."""
        diagnostics_schema = schema["properties"]["diagnostics"]
        required_diag_keys = ["aic", "bic", "log_likelihood", "residual_df"]
        for key in required_diag_keys:
            assert key in diagnostics_schema.get("required", []), \
                f"Diagnostics must require '{key}'"