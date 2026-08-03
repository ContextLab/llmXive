"""
Unit tests for the schema validation framework.
Tests validate that ExecutionRun and RegressionModel structures are correctly validated.
"""
import pytest
from datetime import datetime
from code.tests.contract.validator import (
    validate_schema,
    validate_execution_run,
    validate_regression_model,
    SchemaValidationError
)
from code.tests.contract.schemas import EXECUTION_RUN_SCHEMA, REGRESSION_MODEL_SCHEMA

# Valid ExecutionRun data
VALID_EXECUTION_RUN = {
    "run_id": "run-20231015-001",
    "timestamp": "2023-10-15T10:30:00Z",
    "node_count": 10,
    "granularity": "medium",
    "total_tasks": 100,
    "completed_tasks": 98,
    "failed_tasks": 2,
    "start_time": "2023-10-15T10:30:00Z",
    "end_time": "2023-10-15T11:45:00Z",
    "status": "completed",
    "network_conditions": {
        "latency_ms": 50.0,
        "packet_loss_pct": 0.5
    },
    "metrics": {
        "throughput_tasks_per_sec": 15.5,
        "avg_cpu_utilization_pct": 75.2,
        "coordination_overhead_ratio": 0.12,
        "heterogeneity_penalty": 0.05
    }
}

# Valid RegressionModel data
VALID_REGRESSION_MODEL = {
    "model_type": "MLR",
    "r_squared": 0.85,
    "coefficients": {
        "heterogeneity": -0.5,
        "granularity": 2.3,
        "latency": -0.8,
        "intercept": 10.0
    },
    "p_values": {
        "heterogeneity": 0.001,
        "granularity": 0.02,
        "latency": 0.005,
        "intercept": 0.0001
    },
    "feature_names": ["heterogeneity", "granularity", "latency", "intercept"],
    "n_observations": 500,
    "theoretical_bound": 100.0,
    "bound_violation_flag": False,
    "interaction_terms": ["heterogeneity:granularity"]
}

class TestExecutionRunValidation:
    def test_valid_execution_run(self):
        """Test that a valid ExecutionRun passes validation."""
        result = validate_execution_run(VALID_EXECUTION_RUN)
        assert result is True

    def test_missing_required_field(self):
        """Test that missing required fields raise an error."""
        invalid_data = VALID_EXECUTION_RUN.copy()
        del invalid_data["run_id"]
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_execution_run(invalid_data)
        
        assert "run_id" in str(exc_info.value)

    def test_invalid_granularity_value(self):
        """Test that invalid enum values are rejected."""
        invalid_data = VALID_EXECUTION_RUN.copy()
        invalid_data["granularity"] = "invalid_granularity"
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_execution_run(invalid_data)
        
        assert "invalid_granularity" in str(exc_info.value)

    def test_negative_node_count(self):
        """Test that negative node counts are rejected."""
        invalid_data = VALID_EXECUTION_RUN.copy()
        invalid_data["node_count"] = -5
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_execution_run(invalid_data)
        
        assert "minimum" in str(exc_info.value)

    def test_invalid_status(self):
        """Test that invalid status values are rejected."""
        invalid_data = VALID_EXECUTION_RUN.copy()
        invalid_data["status"] = "unknown_status"
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_execution_run(invalid_data)
        
        assert "unknown_status" in str(exc_info.value)

    def test_missing_network_conditions(self):
        """Test that missing required nested fields are caught."""
        invalid_data = VALID_EXECUTION_RUN.copy()
        invalid_data["network_conditions"] = {"latency_ms": 50.0}  # Missing packet_loss_pct
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_execution_run(invalid_data)
        
        assert "packet_loss_pct" in str(exc_info.value)

class TestRegressionModelValidation:
    def test_valid_regression_model(self):
        """Test that a valid RegressionModel passes validation."""
        result = validate_regression_model(VALID_REGRESSION_MODEL)
        assert result is True

    def test_missing_coefficients(self):
        """Test that missing coefficients field raises an error."""
        invalid_data = VALID_REGRESSION_MODEL.copy()
        del invalid_data["coefficients"]
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_regression_model(invalid_data)
        
        assert "coefficients" in str(exc_info.value)

    def test_invalid_model_type(self):
        """Test that invalid model types are rejected."""
        invalid_data = VALID_REGRESSION_MODEL.copy()
        invalid_data["model_type"] = "INVALID_TYPE"
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_regression_model(invalid_data)
        
        assert "INVALID_TYPE" in str(exc_info.value)

    def test_r_squared_out_of_range(self):
        """Test that R-squared values outside [0, 1] are rejected."""
        invalid_data = VALID_REGRESSION_MODEL.copy()
        invalid_data["r_squared"] = 1.5
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_regression_model(invalid_data)
        
        assert "maximum" in str(exc_info.value)

    def test_negative_n_observations(self):
        """Test that negative observation counts are rejected."""
        invalid_data = VALID_REGRESSION_MODEL.copy()
        invalid_data["n_observations"] = -10
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_regression_model(invalid_data)
        
        assert "minimum" in str(exc_info.value)

    def test_unexpected_property(self):
        """Test that unexpected properties are rejected when additionalProperties is false."""
        invalid_data = VALID_REGRESSION_MODEL.copy()
        invalid_data["unexpected_field"] = "should_fail"
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_regression_model(invalid_data)
        
        assert "unexpected_field" in str(exc_info.value)

class TestSchemaLoading:
    def test_execution_run_schema_structure(self):
        """Test that the ExecutionRun schema has the required structure."""
        assert EXECUTION_RUN_SCHEMA["type"] == "object"
        assert "required" in EXECUTION_RUN_SCHEMA
        assert "properties" in EXECUTION_RUN_SCHEMA
        assert "run_id" in EXECUTION_RUN_SCHEMA["properties"]

    def test_regression_model_schema_structure(self):
        """Test that the RegressionModel schema has the required structure."""
        assert REGRESSION_MODEL_SCHEMA["type"] == "object"
        assert "required" in REGRESSION_MODEL_SCHEMA
        assert "properties" in REGRESSION_MODEL_SCHEMA
        assert "coefficients" in REGRESSION_MODEL_SCHEMA["properties"]