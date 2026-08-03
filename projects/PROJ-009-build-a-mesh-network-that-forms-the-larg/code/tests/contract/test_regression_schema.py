"""
Contract test for RegressionModel JSON output schema.
Implements T028.
"""
import pytest
from orchestrator.contract_validator import validate_schema

def test_regression_model_schema_valid():
    """Test that a valid RegressionModel passes schema validation."""
    data = {
        "model_id": "mlr-001",
        "r_squared": 0.85,
        "coefficients": {
            "heterogeneity": 0.5,
            "granularity": 0.2
        },
        "p_values": {
            "heterogeneity": 0.01,
            "granularity": 0.05
        }
    }
    assert validate_schema(data, "RegressionModel") is True

def test_regression_model_schema_missing_coefficients():
    """Test that missing coefficients raises an error."""
    data = {
        "model_id": "mlr-001",
        "r_squared": 0.85
        # Missing coefficients
    }
    with pytest.raises(ValueError, match="Missing required field"):
        validate_schema(data, "RegressionModel")
