"""
Contract tests for correlation output schema.
"""
import pytest
from typing import Dict, Any, List

def validate_correlation_report(report: Dict[str, Any]) -> bool:
    """
    Validate a correlation report against the expected schema.
    
    Args:
        report: Dictionary to validate
    
    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        'correlation',
        'p_value',
        'is_significant',
        'is_negative',
        'significant_negative',
        'interpretation',
        'sample_size'
    ]
    
    # Check required fields
    for field in required_fields:
        if field not in report:
            return False
    
    # Validate types
    if not isinstance(report['correlation'], (int, float)):
        return False
    
    if not isinstance(report['p_value'], (int, float)):
        return False
    
    if not isinstance(report['is_significant'], bool):
        return False
    
    if not isinstance(report['is_negative'], bool):
        return False
    
    if not isinstance(report['significant_negative'], bool):
        return False
    
    if not isinstance(report['interpretation'], str):
        return False
    
    if not isinstance(report['sample_size'], int):
        return False
    
    return True

def test_correlation_output_schema():
    """Test that a valid correlation report passes validation."""
    valid_report = {
        'correlation': -0.65,
        'p_value': 0.01,
        'is_significant': True,
        'is_negative': True,
        'significant_negative': True,
        'interpretation': 'Significant Negative Correlation',
        'sample_size': 100
    }
    
    assert validate_correlation_report(valid_report) is True

def test_correlation_output_invalid_type():
    """Test that a report with invalid type fails validation."""
    invalid_report = {
        'correlation': "not_a_number",  # Invalid
        'p_value': 0.01,
        'is_significant': True,
        'is_negative': True,
        'significant_negative': True,
        'interpretation': 'Significant Negative Correlation',
        'sample_size': 100
    }
    
    assert validate_correlation_report(invalid_report) is False
