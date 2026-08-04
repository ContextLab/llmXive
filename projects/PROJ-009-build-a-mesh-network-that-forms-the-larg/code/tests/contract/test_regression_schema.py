"""
Contract tests for RegressionModel JSON schema.

These tests verify that RegressionModel output from the analysis
module conforms to the expected schema, ensuring data integrity
for reporting and validation.
"""
import pytest
from orchestrator.contract_validator import validate_schema
from code.tests.contract.schemas import REGRESSION_MODEL_SCHEMA


def test_regression_model_schema_valid():
    """Test that a valid RegressionModel passes schema validation."""
    valid_data = {
        "model_id": "regression-model-001",
        "model_type": "MLR",
        "r_squared": 0.875,
        "coefficients": {
            "intercept": 125.5,
            "node_count": 12.3,
            "granularity_fine": -15.2,
            "granularity_coarse": 25.8,
            "injected_latency": -0.45
        },
        "p_values": {
            "intercept": 0.0001,
            "node_count": 0.001,
            "granularity_fine": 0.025,
            "granularity_coarse": 0.008,
            "injected_latency": 0.003
        },
        "interaction_terms": [
            "node_count:granularity_fine",
            "node_count:granularity_coarse"
        ],
        "theoretical_bound": 3000.0,
        "bound_violation_flag": False,
        "adjusted_r_squared": 0.85,
        "sample_size": 150
    }
    
    errors = validate_schema(valid_data, REGRESSION_MODEL_SCHEMA)
    assert len(errors) == 0, f"Unexpected validation errors: {errors}"


def test_regression_model_schema_missing_coefficients():
    """Test that missing coefficients cause validation failure."""
    invalid_data = {
        "model_id": "regression-model-002",
        "model_type": "GAM",
        "r_squared": 0.82,
        # Missing coefficients (required)
        "p_values": {"intercept": 0.05},
        "interaction_terms": [],
        "theoretical_bound": 2800.0,
        "bound_violation_flag": False
    }
    
    errors = validate_schema(invalid_data, REGRESSION_MODEL_SCHEMA)
    assert len(errors) > 0
    assert any("coefficients" in err for err in errors)