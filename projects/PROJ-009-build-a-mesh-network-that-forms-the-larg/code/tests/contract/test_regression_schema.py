"""
Contract tests specifically for RegressionModel schema.

These tests verify that the RegressionModel structure conforms to the
defined schema and handles edge cases correctly.
"""

import pytest
from orchestrator.contract_validator import validate_schema
from code.tests.contract.schemas import REGRESSION_MODEL_SCHEMA


def test_regression_model_schema_valid():
    """Test that a valid RegressionModel passes validation."""
    valid_model = {
        "coefficients": {
            "intercept": 100.5,
            "heterogeneity": -5.2,
            "granularity": 12.3,
            "injected_latency": -2.1
        },
        "p_values": {
            "intercept": 0.001,
            "heterogeneity": 0.04,
            "granularity": 0.02,
            "injected_latency": 0.03
        },
        "r_squared": 0.85,
        "model_type": "MLR",
        "interaction_terms": ["heterogeneity:granularity"]
    }
    
    # Validate against schema
    validate_schema(valid_model, REGRESSION_MODEL_SCHEMA)
    # Should not raise
    assert True
    
    
def test_regression_model_schema_missing_coefficients():
    """Test that missing coefficients are caught."""
    incomplete_model = {
        "p_values": {"intercept": 0.001},
        "r_squared": 0.85
    }
    
    with pytest.raises(Exception) as exc_info:
        validate_schema(incomplete_model, REGRESSION_MODEL_SCHEMA)
        
    assert "Missing required field" in str(exc_info.value)
    
    
def test_regression_model_schema_invalid_r_squared():
    """Test that R-squared outside valid range is caught."""
    invalid_model = {
        "coefficients": {"intercept": 100.0},
        "p_values": {"intercept": 0.05},
        "r_squared": -0.5  # Negative R-squared
    }
    
    with pytest.raises(Exception) as exc_info:
        validate_schema(invalid_model, REGRESSION_MODEL_SCHEMA)
        
    assert "below minimum" in str(exc_info.value).lower()
    
    
def test_regression_model_schema_invalid_type():
    """Test that invalid types are caught."""
    invalid_model = {
        "coefficients": "not_a_dict",  # Should be dict
        "p_values": {"intercept": 0.05},
        "r_squared": 0.85
    }
    
    with pytest.raises(Exception) as exc_info:
        validate_schema(invalid_model, REGRESSION_MODEL_SCHEMA)
        
    assert "invalid type" in str(exc_info.value).lower()
