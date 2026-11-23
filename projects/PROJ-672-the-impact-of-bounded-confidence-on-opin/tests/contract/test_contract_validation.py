"""
Contract testing framework setup.
This module provides utilities to validate data artifacts against JSON schemas.
It does not run specific domain tests yet, but establishes the framework for
validating SimulationRun, ScalingResult, and RegressionResult artifacts
defined in code/contracts/.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple
import jsonschema
import pytest

# Import schema helpers from the code directory
# We assume the project root is added to sys.path in conftest.py
from contracts.simulation_run import get_simulation_run_schema, validate_simulation_run
from contracts.scaling_result import get_scaling_result_schema, validate_scaling_result
from contracts.regression_result import get_regression_result_schema, validate_regression_result

class ContractValidator:
    """
    A utility class to validate JSON data files against their corresponding schemas.
    """

    def __init__(self, schema_map: Dict[str, Dict[str, Any]]):
        """
        Initialize the validator with a mapping of schema names to their JSON schemas.
        """
        self.schema_map = schema_map

    def validate_file(self, file_path: Path, schema_name: str) -> Tuple[bool, str]:
        """
        Validates a JSON file against a specific schema.
        Returns (is_valid, error_message).
        """
        if not file_path.exists():
            return False, f"File not found: {file_path}"

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON in {file_path}: {str(e)}"

        schema = self.schema_map.get(schema_name)
        if not schema:
            return False, f"Schema not found: {schema_name}"

        try:
            jsonschema.validate(instance=data, schema=schema)
            return True, "Validation successful"
        except jsonschema.ValidationError as e:
            return False, f"Schema validation failed for {file_path}: {e.message}"

    def validate_directory(self, directory: Path, schema_name: str, pattern: str = "*.json") -> List[Tuple[Path, bool, str]]:
        """
        Validates all JSON files in a directory matching a pattern.
        Returns a list of (file_path, is_valid, message) tuples.
        """
        results = []
        for file_path in directory.glob(pattern):
            is_valid, message = self.validate_file(file_path, schema_name)
            results.append((file_path, is_valid, message))
        return results

@pytest.fixture
def simulation_validator():
    """
    Fixture providing a validator for SimulationRun artifacts.
    """
    schema = get_simulation_run_schema()
    return ContractValidator({"SimulationRun": schema})

@pytest.fixture
def scaling_validator():
    """
    Fixture providing a validator for ScalingResult artifacts.
    """
    schema = get_scaling_result_schema()
    return ContractValidator({"ScalingResult": schema})

@pytest.fixture
def regression_validator():
    """
    Fixture providing a validator for RegressionResult artifacts.
    """
    schema = get_regression_result_schema()
    return ContractValidator({"RegressionResult": schema})

# Placeholder tests to ensure the framework is loaded and schemas exist.
# Actual data validation tests will be added as data artifacts are generated.

def test_simulation_schema_exists():
    """Verify that the SimulationRun schema is loadable."""
    try:
        schema = get_simulation_run_schema()
        assert "type" in schema
    except Exception as e:
        pytest.fail(f"Failed to load SimulationRun schema: {e}")

def test_scaling_schema_exists():
    """Verify that the ScalingResult schema is loadable."""
    try:
        schema = get_scaling_result_schema()
        assert "type" in schema
    except Exception as e:
        pytest.fail(f"Failed to load ScalingResult schema: {e}")

def test_regression_schema_exists():
    """Verify that the RegressionResult schema is loadable."""
    try:
        schema = get_regression_result_schema()
        assert "type" in schema
    except Exception as e:
        pytest.fail(f"Failed to load RegressionResult schema: {e}")

def test_validator_initialization(simulation_validator, scaling_validator, regression_validator):
    """Verify that validators can be initialized."""
    assert simulation_validator is not None
    assert scaling_validator is not None
    assert regression_validator is not None
