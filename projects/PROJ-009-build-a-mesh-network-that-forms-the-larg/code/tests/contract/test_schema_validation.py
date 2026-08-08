"""
Unit tests for the schema validation framework (T007).
Tests validate that ExecutionRun and RegressionModel structures are correctly validated.
"""
import pytest
from datetime import datetime
from code.tests.contract.validator import (
    validate_schema,
    validate_execution_run,
    validate_regression_model,
    validate_json_against_schema,
    SchemaValidationError
)
from code.tests.contract.schemas import EXECUTION_RUN_SCHEMA, REGRESSION_MODEL_SCHEMA

class TestSchemaLoading:
    """Tests for loading schemas from the definitions."""

    def test_execution_run_schema_exists(self):
        assert "properties" in EXECUTION_RUN_SCHEMA
        assert "required" in EXECUTION_RUN_SCHEMA
        assert "node_count" in EXECUTION_RUN_SCHEMA["properties"]

    def test_regression_model_schema_exists(self):
        assert "properties" in REGRESSION_MODEL_SCHEMA
        assert "required" in REGRESSION_MODEL_SCHEMA
        assert "r_squared" in REGRESSION_MODEL_SCHEMA["properties"]

class TestExecutionRunValidation:
    """Tests for ExecutionRun validation logic."""

    def test_valid_execution_run(self):
        valid_data = {
            "node_count": 10,
            "granularity": "medium",
            "throughput": 1500.5,
            "overhead_ratio": 0.12,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        # Should not raise
        validate_execution_run(valid_data)

    def test_missing_required_field(self):
        invalid_data = {
            "node_count": 10,
            "granularity": "medium",
            # missing throughput
            "overhead_ratio": 0.12,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        with pytest.raises(SchemaValidationError):
            validate_execution_run(invalid_data)

    def test_invalid_enum_value(self):
        invalid_data = {
            "node_count": 10,
            "granularity": "super_fine",  # Not in enum
            "throughput": 1500.5,
            "overhead_ratio": 0.12,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        with pytest.raises(SchemaValidationError):
            validate_execution_run(invalid_data)

    def test_negative_throughput(self):
        invalid_data = {
            "node_count": 10,
            "granularity": "fine",
            "throughput": -50.0,  # Must be positive
            "overhead_ratio": 0.12,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        with pytest.raises(SchemaValidationError):
            validate_execution_run(invalid_data)

    def test_string_node_count(self):
        invalid_data = {
            "node_count": "ten",  # Should be integer
            "granularity": "fine",
            "throughput": 1500.5,
            "overhead_ratio": 0.12,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        with pytest.raises(SchemaValidationError):
            validate_execution_run(invalid_data)

class TestRegressionModelValidation:
    """Tests for RegressionModel validation logic."""

    def test_valid_regression_model(self):
        valid_data = {
            "model_type": "MLR",
            "coefficients": {"intercept": 10.5, "node_count": 2.3},
            "p_values": {"intercept": 0.01, "node_count": 0.005},
            "r_squared": 0.85,
            "residuals": [0.1, -0.2, 0.05],
            "theoretical_bound_deviation": 0.02
        }
        validate_regression_model(valid_data)

    def test_missing_coefficients(self):
        invalid_data = {
            "model_type": "GAM",
            # missing coefficients
            "p_values": {"intercept": 0.01},
            "r_squared": 0.85,
            "residuals": [0.1],
            "theoretical_bound_deviation": 0.02
        }
        with pytest.raises(SchemaValidationError):
            validate_regression_model(invalid_data)

    def test_invalid_r_squared_range(self):
        invalid_data = {
            "model_type": "MLR",
            "coefficients": {"intercept": 10.5},
            "p_values": {"intercept": 0.01},
            "r_squared": 1.5,  # Must be <= 1.0
            "residuals": [0.1],
            "theoretical_bound_deviation": 0.02
        }
        with pytest.raises(SchemaValidationError):
            validate_regression_model(invalid_data)

    def test_p_value_out_of_range(self):
        invalid_data = {
            "model_type": "MLR",
            "coefficients": {"intercept": 10.5},
            "p_values": {"intercept": 1.5},  # Must be <= 1.0
            "r_squared": 0.85,
            "residuals": [0.1],
            "theoretical_bound_deviation": 0.02
        }
        with pytest.raises(SchemaValidationError):
            validate_regression_model(invalid_data)

class TestDirectSchemaValidation:
    """Tests for the generic validate_json_against_schema utility."""

    def test_string_input(self):
        schema = {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}
        json_str = '{"name": "test"}'
        assert validate_json_against_schema(json_str, schema) is True

    def test_dict_input(self):
        schema = {"type": "object", "properties": {"value": {"type": "integer"}}, "required": ["value"]}
        data = {"value": 42}
        assert validate_json_against_schema(data, schema) is True

    def test_invalid_json_string(self):
        schema = {"type": "object"}
        invalid_str = '{invalid json}'
        with pytest.raises(SchemaValidationError):
            validate_json_against_schema(invalid_str, schema)

    def test_mismatched_schema(self):
        schema = {"type": "object", "properties": {"count": {"type": "integer"}}, "required": ["count"]}
        data = {"count": "not an integer"}
        with pytest.raises(SchemaValidationError):
            validate_json_against_schema(data, schema)