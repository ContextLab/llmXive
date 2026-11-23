"""
Contract tests to validate that data artifacts conform to JSON schemas.

These tests ensure that the data produced by the pipeline matches the
defined schemas (T007). They do not run the simulation logic, only
validate the structure of existing or generated data against schemas.
"""
import json
from pathlib import Path

import pytest
from jsonschema import validate, ValidationError, Draft7Validator

# Import project root path from conftest
from tests.conftest import project_root_path


def load_schema(schema_name: str) -> dict:
    """Load a JSON schema from the contracts directory."""
    schema_path = project_root_path / "code" / "contracts" / schema_name
    if not schema_path.exists():
        pytest.fail(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return json.load(f)


def load_json_data(data_path: Path) -> dict:
    """Load JSON data from a file path."""
    if not data_path.exists():
        pytest.fail(f"Data file not found: {data_path}")
    with open(data_path, "r") as f:
        return json.load(f)


class TestSimulationRunSchema:
    """Tests for the SimulationRun JSON schema."""

    @pytest.fixture
    def schema(self):
        return load_schema("simulation_run.json")

    def test_schema_valid_syntax(self, schema):
        """Ensure the schema itself is valid JSON Schema."""
        Draft7Validator.check_schema(schema)

    # Note: Actual data validation requires generated data.
    # This test framework is set up to run when data exists.
    # We include a placeholder test to ensure the test suite runs.
    def test_schema_structure(self, schema):
        """Verify the schema has expected top-level keys."""
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema


class TestScalingResultSchema:
    """Tests for the ScalingResult JSON schema."""

    @pytest.fixture
    def schema(self):
        return load_schema("scaling_result.json")

    def test_schema_valid_syntax(self, schema):
        """Ensure the schema itself is valid JSON Schema."""
        Draft7Validator.check_schema(schema)

    def test_schema_structure(self, schema):
        """Verify the schema has expected top-level keys."""
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema


class TestRegressionResultSchema:
    """Tests for the RegressionResult JSON schema."""

    @pytest.fixture
    def schema(self):
        return load_schema("regression_result.json")

    def test_schema_valid_syntax(self, schema):
        """Ensure the schema itself is valid JSON Schema."""
        Draft7Validator.check_schema(schema)

    def test_schema_structure(self, schema):
        """Verify the schema has expected top-level keys."""
        assert "type" in schema
        assert schema["type"] == "object"
        assert "properties" in schema


class TestContractValidation:
    """
    Integration-style contract tests that validate real data files if they exist.
    These will skip if data files are not yet generated.
    """

    def test_validate_simulation_run_if_exists(self, contracts_dir):
        """Validate a sample simulation_run.json if it exists."""
        # This is a placeholder for when data is generated.
        # In a real CI/CD, this would point to actual generated files.
        sample_file = contracts_dir.parent.parent.parent / "data" / "raw" / "simulations" / "sample_run.json"
        if not sample_file.exists():
            pytest.skip("Sample simulation run data not yet generated.")

        schema = load_schema("simulation_run.json")
        data = load_json_data(sample_file)
        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Data validation failed: {e.message}")

    def test_validate_scaling_result_if_exists(self, contracts_dir):
        """Validate a sample scaling_result.json if it exists."""
        sample_file = contracts_dir.parent.parent.parent / "data" / "processed" / "sample_scaling.json"
        if not sample_file.exists():
            pytest.skip("Sample scaling result data not yet generated.")

        schema = load_schema("scaling_result.json")
        data = load_json_data(sample_file)
        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Data validation failed: {e.message}")

    def test_validate_regression_result_if_exists(self, contracts_dir):
        """Validate a sample regression_result.json if it exists."""
        sample_file = contracts_dir.parent.parent.parent / "data" / "processed" / "sample_regression.json"
        if not sample_file.exists():
            pytest.skip("Sample regression result data not yet generated.")

        schema = load_schema("regression_result.json")
        data = load_json_data(sample_file)
        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            pytest.fail(f"Data validation failed: {e.message}")
