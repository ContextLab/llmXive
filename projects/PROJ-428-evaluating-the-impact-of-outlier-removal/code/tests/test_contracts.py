"""
Contract tests for Dataset and ContaminationProfile schemas.

These tests validate that data produced by the pipeline conforms to the
expected JSON schemas defined in the contracts directory.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

# Import the validator utilities from the project's src module
from src.validators import load_schema, validate_data, SchemaValidationError


# ----------------------------------------------------------------------
# Helper: Load a schema from the contracts directory
# ----------------------------------------------------------------------
def get_contract_path(contract_name: str) -> Path:
    """Return the absolute path to a contract schema file."""
    # Assume contracts are located at code/contracts relative to project root
    # The test is run from code/ or project root, so we resolve relative to this file
    base_dir = Path(__file__).resolve().parent.parent
    contracts_dir = base_dir / "contracts"
    if not contracts_dir.exists():
        # Fallback: try relative to current working directory
        contracts_dir = Path("contracts")
    return contracts_dir / f"{contract_name}.schema.yaml"


def load_contract_schema(contract_name: str) -> Dict[str, Any]:
    """Load and return the schema for a given contract name."""
    schema_path = get_contract_path(contract_name)
    if not schema_path.exists():
        raise FileNotFoundError(f"Contract schema not found: {schema_path}")
    return load_schema(schema_path)


# ----------------------------------------------------------------------
# Test: Dataset Schema
# ----------------------------------------------------------------------
class TestDatasetSchema:
    """Contract tests for the Dataset schema."""

    @pytest.fixture
    def dataset_schema(self):
        """Load the Dataset schema."""
        return load_contract_schema("Dataset")

    def test_valid_dataset_structure(self, dataset_schema):
        """Test that a valid dataset record passes validation."""
        valid_record = {
            "dataset_name": "uci_adult",
            "source": "UCI Machine Learning Repository",
            "num_rows": 1000,
            "num_columns": 14,
            "continuous_variables": ["age", "hours-per-week", "capital-gain"],
            "variance_values": {
                "age": 120.5,
                "hours-per-week": 45.2,
                "capital-gain": 1200.0
            },
            "file_path": "data/processed/uci_adult_clean.csv"
        }

        try:
            validate_data(valid_record, dataset_schema)
        except SchemaValidationError as e:
            pytest.fail(f"Valid dataset record failed validation: {e}")

    def test_missing_required_field(self, dataset_schema):
        """Test that a record missing a required field fails validation."""
        invalid_record = {
            "dataset_name": "uci_adult",
            # Missing 'source', 'num_rows', etc.
            "continuous_variables": ["age"],
            "variance_values": {"age": 120.5}
        }

        with pytest.raises(SchemaValidationError):
            validate_data(invalid_record, dataset_schema)

    def test_wrong_type_for_field(self, dataset_schema):
        """Test that a record with wrong field types fails validation."""
        invalid_record = {
            "dataset_name": "uci_adult",
            "source": "UCI Machine Learning Repository",
            "num_rows": "not_a_number",  # Should be int
            "num_columns": 14,
            "continuous_variables": ["age", "hours-per-week"],
            "variance_values": {"age": 120.5},
            "file_path": "data/processed/uci_adult_clean.csv"
        }

        with pytest.raises(SchemaValidationError):
            validate_data(invalid_record, dataset_schema)

    def test_missing_continuous_variables(self, dataset_schema):
        """Test that missing continuous_variables list fails validation."""
        invalid_record = {
            "dataset_name": "uci_adult",
            "source": "UCI Machine Learning Repository",
            "num_rows": 1000,
            "num_columns": 14,
            # Missing 'continuous_variables'
            "variance_values": {"age": 120.5},
            "file_path": "data/processed/uci_adult_clean.csv"
        }

        with pytest.raises(SchemaValidationError):
            validate_data(invalid_record, dataset_schema)

    def test_empty_continuous_variables(self, dataset_schema):
        """Test that an empty continuous_variables list fails validation."""
        invalid_record = {
            "dataset_name": "uci_adult",
            "source": "UCI Machine Learning Repository",
            "num_rows": 1000,
            "num_columns": 14,
            "continuous_variables": [],  # Should have at least one
            "variance_values": {},
            "file_path": "data/processed/uci_adult_clean.csv"
        }

        with pytest.raises(SchemaValidationError):
            validate_data(invalid_record, dataset_schema)


# ----------------------------------------------------------------------
# Test: ContaminationProfile Schema
# ----------------------------------------------------------------------
class TestContaminationProfileSchema:
    """Contract tests for the ContaminationProfile schema."""

    @pytest.fixture
    def contamination_schema(self):
        """Load the ContaminationProfile schema."""
        return load_contract_schema("ContaminationProfile")

    def test_valid_contamination_profile(self, contamination_schema):
        """Test that a valid contamination profile passes validation."""
        valid_profile = {
            "dataset_name": "synthetic_normal",
            "contamination_rate": 0.1,
            "method": "cauchy",
            "parameters": {
                "scale": 10.0,
                "location": 0.0
            },
            "injected_outliers_count": 100,
            "total_rows": 1000,
            "affected_columns": ["variable_1"],
            "timestamp": "2023-10-01T12:00:00Z"
        }

        try:
            validate_data(valid_profile, contamination_schema)
        except SchemaValidationError as e:
            pytest.fail(f"Valid contamination profile failed validation: {e}")

    def test_missing_required_field(self, contamination_schema):
        """Test that a profile missing a required field fails validation."""
        invalid_profile = {
            "dataset_name": "synthetic_normal",
            # Missing 'contamination_rate', 'method', etc.
            "parameters": {"scale": 10.0}
        }

        with pytest.raises(SchemaValidationError):
            validate_data(invalid_profile, contamination_schema)

    def test_wrong_type_for_contamination_rate(self, contamination_schema):
        """Test that a non-float contamination_rate fails validation."""
        invalid_profile = {
            "dataset_name": "synthetic_normal",
            "contamination_rate": "0.1",  # Should be float
            "method": "cauchy",
            "parameters": {"scale": 10.0},
            "injected_outliers_count": 100,
            "total_rows": 1000,
            "affected_columns": ["variable_1"],
            "timestamp": "2023-10-01T12:00:00Z"
        }

        with pytest.raises(SchemaValidationError):
            validate_data(invalid_profile, contamination_schema)

    def test_contamination_rate_out_of_range(self, contamination_schema):
        """Test that a contamination_rate outside [0, 1] fails validation."""
        invalid_profile = {
            "dataset_name": "synthetic_normal",
            "contamination_rate": 1.5,  # Should be between 0 and 1
            "method": "cauchy",
            "parameters": {"scale": 10.0},
            "injected_outliers_count": 100,
            "total_rows": 1000,
            "affected_columns": ["variable_1"],
            "timestamp": "2023-10-01T12:00:00Z"
        }

        with pytest.raises(SchemaValidationError):
            validate_data(invalid_profile, contamination_schema)

    def test_missing_parameters(self, contamination_schema):
        """Test that missing parameters dict fails validation."""
        invalid_profile = {
            "dataset_name": "synthetic_normal",
            "contamination_rate": 0.1,
            "method": "cauchy",
            # Missing 'parameters'
            "injected_outliers_count": 100,
            "total_rows": 1000,
            "affected_columns": ["variable_1"],
            "timestamp": "2023-10-01T12:00:00Z"
        }

        with pytest.raises(SchemaValidationError):
            validate_data(invalid_profile, contamination_schema)

    def test_empty_affected_columns(self, contamination_schema):
        """Test that empty affected_columns list fails validation."""
        invalid_profile = {
            "dataset_name": "synthetic_normal",
            "contamination_rate": 0.1,
            "method": "cauchy",
            "parameters": {"scale": 10.0},
            "injected_outliers_count": 100,
            "total_rows": 1000,
            "affected_columns": [],  # Should have at least one
            "timestamp": "2023-10-01T12:00:00Z"
        }

        with pytest.raises(SchemaValidationError):
            validate_data(invalid_profile, contamination_schema)

    def test_invalid_method(self, contamination_schema):
        """Test that an unsupported method fails validation."""
        invalid_profile = {
            "dataset_name": "synthetic_normal",
            "contamination_rate": 0.1,
            "method": "invalid_method",  # Not in enum
            "parameters": {"scale": 10.0},
            "injected_outliers_count": 100,
            "total_rows": 1000,
            "affected_columns": ["variable_1"],
            "timestamp": "2023-10-01T12:00:00Z"
        }

        with pytest.raises(SchemaValidationError):
            validate_data(invalid_profile, contamination_schema)


# ----------------------------------------------------------------------
# Integration Test: Load and validate real JSON files if they exist
# ----------------------------------------------------------------------
def test_dataset_schema_integration():
    """
    Integration test: Validate real Dataset JSON files from data/results
    if they exist.
    """
    schema = load_contract_schema("Dataset")
    data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "results"
    dataset_files = list(data_dir.glob("*.json"))

    if not dataset_files:
        # If no files exist, this test is skipped (not a failure)
        pytest.skip("No Dataset JSON files found in data/results")

    for file_path in dataset_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Some files might be aggregated results, not single datasets
            # We expect the data to be a list of dataset records or a single record
            if isinstance(data, list):
                for record in data:
                    validate_data(record, schema)
            else:
                validate_data(data, schema)
        except json.JSONDecodeError:
            pytest.fail(f"File {file_path} is not valid JSON")
        except SchemaValidationError as e:
            pytest.fail(f"File {file_path} failed schema validation: {e}")


def test_contamination_profile_schema_integration():
    """
    Integration test: Validate real ContaminationProfile JSON files from
    data/processed if they exist.
    """
    schema = load_contract_schema("ContaminationProfile")
    data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "processed"
    profile_files = list(data_dir.glob("injection_profile*.json"))

    if not profile_files:
        pytest.skip("No ContaminationProfile JSON files found in data/processed")

    for file_path in profile_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                for record in data:
                    validate_data(record, schema)
            else:
                validate_data(data, schema)
        except json.JSONDecodeError:
            pytest.fail(f"File {file_path} is not valid JSON")
        except SchemaValidationError as e:
            pytest.fail(f"File {file_path} failed schema validation: {e}")