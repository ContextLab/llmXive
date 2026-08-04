"""
Contract tests for data schemas in the Neural Correlates of Predictive Error Signals pipeline.

This module validates that data artifacts conform to the schemas defined in `contracts/`.
It ensures data integrity across the pipeline stages (Ingestion -> Preprocessing -> Alignment -> Modeling).
"""

import json
import os
import pytest
import yaml
from pathlib import Path
from typing import Any, Dict, List

# Project root relative to this file (assuming tests/contract/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Schema file paths
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
MODEL_OUTPUT_SCHEMA_PATH = CONTRACTS_DIR / "model_output.schema.yaml"
ALIGNED_DATA_SCHEMA_PATH = CONTRACTS_DIR / "aligned_data.schema.yaml"

# Output artifact paths for validation
MODEL_OUTPUT_PATH = PROJECT_ROOT / "analysis" / "results" / "model_output.json"
ALIGNED_DATA_PATH = PROJECT_ROOT / "data" / "aligned_data.csv"

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_required_fields(data: Dict[str, Any], required_fields: List[str], context: str) -> None:
    """Validate that all required fields are present in the data."""
    missing = [f for f in required_fields if f not in data]
    if missing:
        raise AssertionError(
            f"Validation failed for {context}: Missing required fields: {missing}"
        )

def validate_field_types(data: Dict[str, Any], type_map: Dict[str, str], context: str) -> None:
    """Validate that fields match expected types."""
    for field, expected_type in type_map.items():
        if field in data:
            value = data[field]
            if expected_type == "string":
                if not isinstance(value, str):
                    raise AssertionError(
                        f"Validation failed for {context}: Field '{field}' expected string, got {type(value)}"
                    )
            elif expected_type == "number":
                if not isinstance(value, (int, float)):
                    raise AssertionError(
                        f"Validation failed for {context}: Field '{field}' expected number, got {type(value)}"
                    )
            elif expected_type == "boolean":
                if not isinstance(value, bool):
                    raise AssertionError(
                        f"Validation failed for {context}: Field '{field}' expected boolean, got {type(value)}"
                    )
            elif expected_type == "array":
                if not isinstance(value, list):
                    raise AssertionError(
                        f"Validation failed for {context}: Field '{field}' expected array, got {type(value)}"
                    )
            elif expected_type == "object":
                if not isinstance(value, dict):
                    raise AssertionError(
                        f"Validation failed for {context}: Field '{field}' expected object, got {type(value)}"
                    )

class TestModelOutputSchema:
    """Contract tests for the model_output.json schema."""

    @pytest.fixture
    def schema(self):
        """Load the model output schema."""
        return load_schema(MODEL_OUTPUT_SCHEMA_PATH)

    def test_schema_file_exists(self):
        """Verify the schema definition file exists."""
        assert MODEL_OUTPUT_SCHEMA_PATH.exists(), f"Schema file missing: {MODEL_OUTPUT_SCHEMA_PATH}"

    def test_schema_structure(self, schema):
        """Verify the schema has the expected structure."""
        assert "type" in schema, "Schema must define 'type'"
        assert "properties" in schema, "Schema must define 'properties'"
        assert "required" in schema, "Schema must define 'required' fields"

    def test_model_output_artifact_exists(self):
        """Verify the model output artifact exists (if analysis was run)."""
        # This test passes if the file exists. If the pipeline hasn't run yet,
        # this might be skipped or expected to fail depending on CI configuration.
        # For contract testing, we assert existence if the file is expected.
        if MODEL_OUTPUT_PATH.exists():
            assert MODEL_OUTPUT_PATH.is_file()
        else:
            # If file doesn't exist, we skip the content validation but note it.
            # In a real CI, this might be a failure if the stage is expected to produce it.
            pytest.skip(f"Model output artifact not found at {MODEL_OUTPUT_PATH}. Analysis may not have run yet.")

    def test_model_output_conforms_to_schema(self):
        """Validate that model_output.json matches the schema."""
        if not MODEL_OUTPUT_PATH.exists():
            pytest.skip("Model output artifact not found.")

        with open(MODEL_OUTPUT_PATH, "r") as f:
            data = json.load(f)

        schema = load_schema(MODEL_OUTPUT_SCHEMA_PATH)

        # Check required fields
        validate_required_fields(data, schema["required"], "model_output.json")

        # Check field types
        type_map = {k: v.get("type", "any") for k, v in schema["properties"].items()}
        validate_field_types(data, type_map, "model_output.json")

        # Specific checks for Gaussian LME output (Plan Correction)
        if "coefficients" in data:
            assert isinstance(data["coefficients"], dict), "coefficients must be an object"
            # Check for expected fixed effects based on T029
            expected_fixed_effects = ["Accuracy", "Learning_Phase"]
            for effect in expected_fixed_effects:
                # The key might be the effect name directly or nested
                if effect not in data["coefficients"]:
                    # Allow for formatting variations, e.g., "Accuracy (1)" or similar
                    matching_keys = [k for k in data["coefficients"].keys() if effect in k]
                    assert len(matching_keys) > 0, f"Missing expected coefficient for {effect}"

        if "p_values" in data:
            assert isinstance(data["p_values"], dict), "p_values must be an object"

        if "permutation_test" in data:
            assert isinstance(data["permutation_test"], dict), "permutation_test must be an object"
            assert "p_value" in data["permutation_test"], "permutation_test must have p_value"
            assert "n_permutations" in data["permutation_test"], "permutation_test must have n_permutations"

        if "robustness" in data:
            assert isinstance(data["robustness"], dict), "robustness must be an object"

class TestAlignedDataSchema:
    """Contract tests for the aligned_data.csv schema."""

    @pytest.fixture
    def schema(self):
        """Load the aligned data schema."""
        return load_schema(ALIGNED_DATA_SCHEMA_PATH)

    def test_schema_file_exists(self):
        """Verify the schema definition file exists."""
        assert ALIGNED_DATA_SCHEMA_PATH.exists(), f"Schema file missing: {ALIGNED_DATA_SCHEMA_PATH}"

    def test_schema_structure(self, schema):
        """Verify the schema has the expected structure."""
        assert "columns" in schema, "Schema must define 'columns'"
        assert isinstance(schema["columns"], list), "columns must be a list"

    def test_aligned_data_artifact_exists(self):
        """Verify the aligned data artifact exists."""
        if ALIGNED_DATA_PATH.exists():
            assert ALIGNED_DATA_PATH.is_file()
        else:
            pytest.skip(f"Aligned data artifact not found at {ALIGNED_DATA_PATH}. US2 may not have run yet.")

    def test_aligned_data_conforms_to_schema(self):
        """Validate that aligned_data.csv matches the schema."""
        if not ALIGNED_DATA_PATH.exists():
            pytest.skip("Aligned data artifact not found.")

        import pandas as pd
        df = pd.read_csv(ALIGNED_DATA_PATH)
        schema = load_schema(ALIGNED_DATA_SCHEMA_PATH)

        expected_columns = [col["name"] for col in schema["columns"]]
        missing_columns = [col for col in expected_columns if col not in df.columns]

        assert not missing_columns, f"Aligned data missing required columns: {missing_columns}"

        # Validate specific column types based on schema
        for col_def in schema["columns"]:
            col_name = col_def["name"]
            col_type = col_def.get("type", "string")
            if col_name in df.columns:
                if col_type == "integer":
                    assert pd.api.types.is_integer_dtype(df[col_name]) or pd.api.types.is_numeric_dtype(df[col_name]), \
                        f"Column {col_name} should be integer/numeric"
                elif col_type == "float":
                    assert pd.api.types.is_float_dtype(df[col_name]) or pd.api.types.is_numeric_dtype(df[col_name]), \
                        f"Column {col_name} should be float/numeric"
                elif col_type == "string":
                    assert df[col_name].dtype == object or pd.api.types.is_string_dtype(df[col_name]), \
                        f"Column {col_name} should be string"

        # Specific checks for Lagged Alignment (T024)
        if "mmn_amplitude" in df.columns:
            assert not df["mmn_amplitude"].isna().all(), "mmn_amplitude cannot be all NaN"
        if "source_window_start_trial" in df.columns:
            assert not df["source_window_start_trial"].isna().all(), "source_window_start_trial cannot be all NaN"

        # Check for analysis_mode flag (T022)
        if "analysis_mode" in df.columns:
            valid_modes = ["error_signal", "stimulus_driven"]
            invalid_modes = df[~df["analysis_mode"].isin(valid_modes)]
            assert len(invalid_modes) == 0, f"Invalid analysis_mode values found: {invalid_modes['analysis_mode'].unique()}"