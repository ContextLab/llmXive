"""
Contract tests for T002: Schema validation.
Verifies that the YAML schemas are valid and can be loaded by the validator utility.
"""
import os
import json
import pytest
from pathlib import Path

# Import the validator utilities from the project
from utils.validators import load_schema, validate_json_against_schema

# Resolve paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

@pytest.fixture
def dataset_schema():
    return load_schema(CONTRACTS_DIR / "dataset.schema.yaml")

@pytest.fixture
def output_schema():
    return load_schema(CONTRACTS_DIR / "output.schema.yaml")

@pytest.fixture
def results_schema():
    return load_schema(CONTRACTS_DIR / "results.schema.yaml")

class TestDatasetSchema:
    def test_schema_loads(self, dataset_schema):
        assert dataset_schema is not None
        assert "properties" in dataset_schema
        assert "participant_id" in dataset_schema["properties"]

    def test_required_fields_present(self, dataset_schema):
        required = dataset_schema.get("required", [])
        assert "participant_id" in required
        assert "pre_self_esteem" in required
        assert "post_self_esteem" in required
        assert "comparison_tendency" in required
        assert "avatar_condition" in required

    def test_valid_data_passes(self, dataset_schema):
        valid_data = {
            "participant_id": "P001",
            "pre_self_esteem": 3.5,
            "post_self_esteem": 3.8,
            "comparison_tendency": 2.1,
            "avatar_condition": 1
        }
        # Validate against the loaded schema
        # Note: validate_json_against_schema expects a dict schema and data
        result = validate_json_against_schema(valid_data, dataset_schema)
        assert result is True

    def test_invalid_data_fails(self, dataset_schema):
        invalid_data = {
            "participant_id": "P001",
            "pre_self_esteem": "not_a_float", # Should be number
            "post_self_esteem": 3.8,
            "comparison_tendency": 2.1,
            "avatar_condition": 1
        }
        with pytest.raises(Exception):
            validate_json_against_schema(invalid_data, dataset_schema)

class TestOutputSchema:
    def test_schema_loads(self, output_schema):
        assert output_schema is not None
        assert "missingness_report" in output_schema["properties"]

    def test_valid_data_passes(self, output_schema):
        valid_data = {
            "imputed_data_checksum": "abc123...",
            "missingness_report": {
                "initial_missing_count": 5,
                "final_missing_count": 0,
                "missing_percentage": 1.2
            }
        }
        result = validate_json_against_schema(valid_data, output_schema)
        assert result is True

class TestResultsSchema:
    def test_schema_loads(self, results_schema):
        assert results_schema is not None
        assert "coefficients" in results_schema["properties"]
        assert "assumptions" in results_schema["properties"]
        assert "data_source_type" in results_schema["properties"]

    def test_valid_data_passes(self, results_schema):
        valid_data = {
            "coefficients": [
                {
                    "name": "intercept",
                    "estimate": 0.5,
                    "std_err": 0.1,
                    "p_value": 0.01
                }
            ],
            "assumptions": {
                "shapiro_p": 0.45,
                "breusch_pagan_p": 0.60,
                "vif_max": 1.2
            },
            "data_source_type": "synthetic"
        }
        result = validate_json_against_schema(valid_data, results_schema)
        assert result is True

    def test_invalid_data_source_type_fails(self, results_schema):
        invalid_data = {
            "coefficients": [],
            "assumptions": {"shapiro_p": 0.5, "breusch_pagan_p": 0.5, "vif_max": 1.0},
            "data_source_type": "fake_data" # Invalid enum value
        }
        with pytest.raises(Exception):
            validate_json_against_schema(invalid_data, results_schema)
