"""
Contract tests for schema validation framework.

These tests ensure that the schema validation framework correctly
validates ExecutionRun and RegressionModel structures.
"""
import pytest
from datetime import datetime
from code.tests.contract.validator import (
    SchemaValidationError,
    validate_execution_run,
    validate_regression_model,
    validate_schema,
    validate_type,
    validate_enum,
    validate_minimum,
    validate_maximum,
    load_schema_from_yaml
)
from code.tests.contract.schemas import EXECUTION_RUN_SCHEMA, REGRESSION_MODEL_SCHEMA


class TestExecutionRunValidation:
    """Tests for ExecutionRun schema validation."""
    
    def test_valid_execution_run(self):
        """Test that a valid ExecutionRun passes validation."""
        valid_data = {
            "run_id": "run-001",
            "timestamp_start": "2024-01-15T10:30:00Z",
            "timestamp_end": "2024-01-15T10:45:00Z",
            "node_count": 10,
            "granularity": "medium",
            "injected_latency_ms": 50.0,
            "packet_loss_rate": 0.02,
            "throughput_ops_sec": 1500.5,
            "coordination_overhead_ratio": 0.15,
            "status": "completed",
            "heterogeneity_index": 0.25,
            "total_compute_time_sec": 900.0,
            "total_coordination_time_sec": 135.0
        }
        
        # Should not raise
        assert validate_execution_run(valid_data) is True
    
    def test_missing_required_field(self):
        """Test that missing required fields cause validation failure."""
        invalid_data = {
            "run_id": "run-002",
            "timestamp_start": "2024-01-15T10:30:00Z",
            # Missing timestamp_end
            "node_count": 10,
            "granularity": "medium",
            "injected_latency_ms": 50.0,
            "packet_loss_rate": 0.02,
            "throughput_ops_sec": 1500.5,
            "coordination_overhead_ratio": 0.15,
            "status": "completed"
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_execution_run(invalid_data)
        
        assert "timestamp_end" in str(exc_info.value)
    
    def test_invalid_enum_value(self):
        """Test that invalid enum values are rejected."""
        invalid_data = {
            "run_id": "run-003",
            "timestamp_start": "2024-01-15T10:30:00Z",
            "timestamp_end": "2024-01-15T10:45:00Z",
            "node_count": 10,
            "granularity": "invalid_granularity",  # Not in enum
            "injected_latency_ms": 50.0,
            "packet_loss_rate": 0.02,
            "throughput_ops_sec": 1500.5,
            "coordination_overhead_ratio": 0.15,
            "status": "completed"
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_execution_run(invalid_data)
        
        assert "granularity" in str(exc_info.value)
    
    def test_negative_number_rejected(self):
        """Test that negative numbers for non-negative fields are rejected."""
        invalid_data = {
            "run_id": "run-004",
            "timestamp_start": "2024-01-15T10:30:00Z",
            "timestamp_end": "2024-01-15T10:45:00Z",
            "node_count": -5,  # Invalid: negative
            "granularity": "medium",
            "injected_latency_ms": 50.0,
            "packet_loss_rate": 0.02,
            "throughput_ops_sec": 1500.5,
            "coordination_overhead_ratio": 0.15,
            "status": "completed"
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_execution_run(invalid_data)
        
        assert "node_count" in str(exc_info.value)
    
    def test_packet_loss_out_of_range(self):
        """Test that packet_loss_rate > 1 is rejected."""
        invalid_data = {
            "run_id": "run-005",
            "timestamp_start": "2024-01-15T10:30:00Z",
            "timestamp_end": "2024-01-15T10:45:00Z",
            "node_count": 10,
            "granularity": "medium",
            "injected_latency_ms": 50.0,
            "packet_loss_rate": 1.5,  # Invalid: > 1
            "throughput_ops_sec": 1500.5,
            "coordination_overhead_ratio": 0.15,
            "status": "completed"
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_execution_run(invalid_data)
        
        assert "packet_loss_rate" in str(exc_info.value)


class TestRegressionModelValidation:
    """Tests for RegressionModel schema validation."""
    
    def test_valid_regression_model(self):
        """Test that a valid RegressionModel passes validation."""
        valid_data = {
            "model_id": "model-001",
            "model_type": "MLR",
            "r_squared": 0.85,
            "coefficients": {
                "intercept": 100.0,
                "node_count": 5.5,
                "granularity_fine": -10.0,
                "granularity_coarse": 20.0,
                "injected_latency": -0.5
            },
            "p_values": {
                "intercept": 0.001,
                "node_count": 0.002,
                "granularity_fine": 0.03,
                "granularity_coarse": 0.01,
                "injected_latency": 0.005
            },
            "interaction_terms": ["node_count:granularity_fine"],
            "theoretical_bound": 2500.0,
            "bound_violation_flag": False
        }
        
        # Should not raise
        assert validate_regression_model(valid_data) is True
    
    def test_missing_coefficients(self):
        """Test that missing coefficients cause validation failure."""
        invalid_data = {
            "model_id": "model-002",
            "model_type": "GAM",
            # Missing coefficients
            "r_squared": 0.82,
            "p_values": {},
            "interaction_terms": [],
            "theoretical_bound": 2500.0,
            "bound_violation_flag": False
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_regression_model(invalid_data)
        
        assert "coefficients" in str(exc_info.value)
    
    def test_invalid_model_type(self):
        """Test that invalid model_type enum is rejected."""
        invalid_data = {
            "model_id": "model-003",
            "model_type": "INVALID_TYPE",
            "r_squared": 0.80,
            "coefficients": {"intercept": 50.0},
            "p_values": {"intercept": 0.05},
            "interaction_terms": [],
            "theoretical_bound": 2500.0,
            "bound_violation_flag": False
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_regression_model(invalid_data)
        
        assert "model_type" in str(exc_info.value)
    
    def test_r_squared_out_of_range(self):
        """Test that r_squared > 1 is rejected."""
        invalid_data = {
            "model_id": "model-004",
            "model_type": "MLR",
            "r_squared": 1.2,  # Invalid: > 1
            "coefficients": {"intercept": 50.0},
            "p_values": {"intercept": 0.05},
            "interaction_terms": [],
            "theoretical_bound": 2500.0,
            "bound_violation_flag": False
        }
        
        with pytest.raises(SchemaValidationError) as exc_info:
            validate_regression_model(invalid_data)
        
        assert "r_squared" in str(exc_info.value)


class TestSchemaLoading:
    """Tests for schema loading functionality."""
    
    def test_load_schema_from_dict(self):
        """Test that schemas can be loaded from the module."""
        assert isinstance(EXECUTION_RUN_SCHEMA, dict)
        assert "required" in EXECUTION_RUN_SCHEMA
        assert "properties" in EXECUTION_RUN_SCHEMA
        
        assert isinstance(REGRESSION_MODEL_SCHEMA, dict)
        assert "required" in REGRESSION_MODEL_SCHEMA
        assert "properties" in REGRESSION_MODEL_SCHEMA
    
    def test_schema_has_required_fields(self):
        """Test that schemas define required fields."""
        exec_required = EXECUTION_RUN_SCHEMA.get("required", [])
        assert "run_id" in exec_required
        assert "throughput_ops_sec" in exec_required
        assert "status" in exec_required
        
        reg_required = REGRESSION_MODEL_SCHEMA.get("required", [])
        assert "model_id" in reg_required
        assert "r_squared" in reg_required
        assert "coefficients" in reg_required
