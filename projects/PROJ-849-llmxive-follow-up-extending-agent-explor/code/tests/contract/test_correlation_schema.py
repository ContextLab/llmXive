"""
Contract tests for the correlation analysis output schema.
Validates the structure of correlation analysis results.
"""
import pytest
from typing import Dict, Any, List


def validate_correlation_report(report: Dict[str, Any]) -> bool:
    """
    Validates a correlation analysis report.

    Expected schema:
    {
        "pearson_correlation": float,
        "p_value": float,
        "sample_size": int,
        "significant_negative_correlation": bool,
        "result_summary": str
    }
    """
    required_fields = {
        "pearson_correlation": (int, float),
        "p_value": (int, float),
        "sample_size": int,
        "significant_negative_correlation": bool,
        "result_summary": str
    }

    if not isinstance(report, dict):
        return False

    for field, expected_type in required_fields.items():
        if field not in report:
            return False
        if not isinstance(report[field], expected_type):
            return False

    return True


def test_correlation_output_schema() -> None:
    """Test that a valid correlation report passes validation."""
    valid_report = {
        "pearson_correlation": -0.65,
        "p_value": 0.001,
        "sample_size": 500,
        "significant_negative_correlation": True,
        "result_summary": "Significant negative correlation detected."
    }
    assert validate_correlation_report(valid_report) is True


def test_correlation_output_invalid_type() -> None:
    """Test that a report with invalid types fails validation."""
    invalid_report = {
        "pearson_correlation": "not a number",
        "p_value": 0.001,
        "sample_size": 500,
        "significant_negative_correlation": True,
        "result_summary": "Significant negative correlation detected."
    }
    assert validate_correlation_report(invalid_report) is False
