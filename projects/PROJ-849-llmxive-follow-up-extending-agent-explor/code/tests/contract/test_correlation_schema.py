import pytest
from typing import Dict, Any, List

def validate_correlation_report(report: Dict[str, Any]) -> bool:
    """Validate the correlation analysis report schema."""
    required_fields = ["correlation", "p_value", "sample_size", "significant_negative"]
    
    for field in required_fields:
        if field not in report:
            return False
    
    if not isinstance(report["correlation"], (int, float)):
        return False
    if not isinstance(report["p_value"], (int, float)):
        return False
    if not isinstance(report["sample_size"], int):
        return False
    if not isinstance(report["significant_negative"], bool):
        return False
        
    return True

def test_correlation_output_schema():
    """Test that the correlation output schema is valid."""
    sample = {
        "correlation": -0.45,
        "p_value": 0.001,
        "sample_size": 100,
        "significant_negative": True
    }
    
    assert validate_correlation_report(sample) is True

def test_correlation_output_invalid_type():
    """Test validation fails on invalid types."""
    sample = {
        "correlation": "invalid",  # Should be float
        "p_value": 0.001,
        "sample_size": 100,
        "significant_negative": True
    }
    
    assert validate_correlation_report(sample) is False
