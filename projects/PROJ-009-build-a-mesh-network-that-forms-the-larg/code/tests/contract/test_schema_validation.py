"""
Contract tests for schema validation of ExecutionRun and RegressionModel.
These tests ensure that the validation framework correctly accepts valid data
and rejects invalid data according to the defined schemas.
"""
import pytest
from datetime import datetime
from code.tests.contract.validator import (
    SchemaValidationError,
    validate_execution_run,
    validate_regression_model,
    validate_schema
)
from code.tests.contract.schemas import EXECUTION_RUN_SCHEMA, REGRESSION_MODEL_SCHEMA


class TestSchemaLoading:
    """Tests for loading schema definitions."""

    def test_execution_run_schema_exists(self):
        """Verify ExecutionRun schema is defined."""
        assert "properties" in EXECUTION_RUN_SCHEMA
        assert "node_count" in EXECUTION_RUN_SCHEMA["properties"]
        assert "granularity" in EXECUTION_RUN_SCHEMA["properties"]

    def test_regression_model_schema_exists(self):
        """Verify RegressionModel schema is defined."""
        assert "properties" in REGRESSION_MODEL_SCHEMA
        assert "coefficients" in REGRESSION_MODEL_SCHEMA["properties"]
        assert "r_squared" in REGRESSION_MODEL_SCHEMA["properties"]


class TestExecutionRunValidation:
    """Tests for ExecutionRun schema validation."""

    def test_valid_execution_run(self):
        """Test that a valid ExecutionRun passes validation."""
        valid_data = {
            "run_id": "run-001",
            "timestamp": datetime.now().isoformat(),
            "node_count": 5,
            "granularity": "medium",
            "throughput": 1250.5,
            "overhead_ratio": 0.15,
            "latency_injected_ms": 50.0,
            "packet_loss_rate": 0.02
        }
        # Should not raise
        validate_execution_run(valid_data)

    def test_missing_required_field(self):
        """Test that missing required fields raise an error."""
        invalid_data = {
            "run_id": "run-002",
            "granularity": "fine",
            "throughput": 1000.0
            # Missing node_count and overhead_ratio
        }
        with pytest.raises(SchemaValidationError, match="Missing required field"):
            validate_execution_run(invalid_data)

    def test_invalid_granularity_enum(self):
        """Test that invalid enum values are rejected."""
        invalid_data = {
            "run_id": "run-003",
            "timestamp": datetime.now().isoformat(),
            "node_count": 3,
            "granularity": "super-fine",  # Invalid enum
            "throughput": 800.0,
            "overhead_ratio": 0.1
        }
        with pytest.raises(SchemaValidationError, match="must be one of"):
            validate_execution_run(invalid_data)

    def test_negative_throughput(self):
        """Test that negative numbers are rejected for throughput."""
        invalid_data = {
            "run_id": "run-004",
            "timestamp": datetime.now().isoformat(),
            "node_count": 4,
            "granularity": "coarse",
            "throughput": -50.0,  # Invalid
            "overhead_ratio": 0.2
        }
        with pytest.raises(SchemaValidationError, match="must be >="):
            validate_execution_run(invalid_data)

    def test_invalid_node_count_type(self):
        """Test that non-integer node_count is rejected."""
        invalid_data = {
            "run_id": "run-005",
            "timestamp": datetime.now().isoformat(),
            "node_count": "five",  # Should be integer
            "granularity": "fine",
            "throughput": 1000.0,
            "overhead_ratio": 0.1
        }
        with pytest.raises(SchemaValidationError, match="must be an integer"):
            validate_execution_run(invalid_data)


class TestRegressionModelValidation:
    """Tests for RegressionModel schema validation."""

    def test_valid_regression_model(self):
        """Test that a valid RegressionModel passes validation."""
        valid_data = {
            "model_id": "model-mlr-001",
            "model_type": "MLR",
            "formula": "throughput ~ heterogeneity * granularity + injected_latency",
            "coefficients": {
                "intercept": 1500.0,
                "heterogeneity": -50.5,
                "granularity_coarse": 200.0,
                "injected_latency": -2.5
            },
            "p_values": {
                "intercept": 0.001,
                "heterogeneity": 0.03,
                "granularity_coarse": 0.005,
                "injected_latency": 0.01
            },
            "r_squared": 0.85,
            "aic": 120.5,
            "bic": 135.2,
            "interaction_terms": ["heterogeneity:granularity"]
        }
        # Should not raise
        validate_regression_model(valid_data)

    def test_missing_coefficients(self):
        """Test that missing coefficients raise an error."""
        invalid_data = {
            "model_id": "model-002",
            "model_type": "GAM",
            "p_values": {"x": 0.05},
            "r_squared": 0.7
            # Missing coefficients
        }
        with pytest.raises(SchemaValidationError, match="Missing required field"):
            validate_regression_model(invalid_data)

    def test_invalid_r_squared_range(self):
        """Test that r_squared outside [0, 1] is rejected."""
        invalid_data = {
            "model_id": "model-003",
            "model_type": "MLR",
            "coefficients": {"x": 1.0},
            "p_values": {"x": 0.05},
            "r_squared": 1.5  # Invalid
        }
        with pytest.raises(SchemaValidationError, match="must be <= 1"):
            validate_regression_model(invalid_data)

    def test_invalid_model_type_enum(self):
        """Test that invalid model_type is rejected."""
        invalid_data = {
            "model_id": "model-004",
            "model_type": "QUADRATIC",  # Invalid
            "coefficients": {"x": 1.0},
            "p_values": {"x": 0.05},
            "r_squared": 0.8
        }
        with pytest.raises(SchemaValidationError, match="must be one of"):
            validate_regression_model(invalid_data)

    def test_coefficients_must_be_numbers(self):
        """Test that coefficient values must be numbers."""
        invalid_data = {
            "model_id": "model-005",
            "model_type": "MLR",
            "coefficients": {
                "x": "not a number"
            },
            "p_values": {"x": 0.05},
            "r_squared": 0.8
        }
        with pytest.raises(SchemaValidationError, match="must be a number"):
            validate_regression_model(invalid_data)


class TestDirectSchemaValidation:
    """Tests for the generic validate_schema function."""

    def test_validate_type_string(self):
        """Test type validation for strings."""
        from code.tests.contract.validator import validate_type
        validate_type("hello", "string", "test_field")
        with pytest.raises(SchemaValidationError):
            validate_type(123, "string", "test_field")

    def test_validate_type_integer(self):
        """Test type validation for integers."""
        from code.tests.contract.validator import validate_type
        validate_type(42, "integer", "test_field")
        with pytest.raises(SchemaValidationError):
            validate_type(3.14, "integer", "test_field")

    def test_validate_enum(self):
        """Test enum validation."""
        from code.tests.contract.validator import validate_enum
        validate_enum("red", ["red", "green", "blue"], "color")
        with pytest.raises(SchemaValidationError):
            validate_enum("yellow", ["red", "green", "blue"], "color")
