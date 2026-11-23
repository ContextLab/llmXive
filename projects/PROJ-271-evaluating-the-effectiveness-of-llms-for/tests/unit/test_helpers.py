"""
Unit tests for helper functions.
"""
import pytest
import pandas as pd
import numpy as np

from code.helpers import (
    compute_radon_metrics_safe,
    validate_dataset_completeness,
    safe_json_parse,
    calculate_statistics
)


def test_compute_radon_metrics_safe_valid_code():
    """Test radon metrics computation with valid code."""
    code = """
    def hello():
        print("Hello")
    """
    metrics = compute_radon_metrics_safe(code)
    
    assert "loc" in metrics
    assert "cyclomatic_complexity" in metrics
    assert metrics["loc"] > 0


def test_compute_radon_metrics_safe_invalid_code():
    """Test radon metrics computation with invalid code."""
    code = "def broken("  # Invalid syntax
    metrics = compute_radon_metrics_safe(code)
    
    assert metrics["loc"] == 0
    assert metrics["cyclomatic_complexity"] == 0


def test_validate_dataset_completeness_full():
    """Test validation with complete dataset."""
    df = pd.DataFrame({
        "code": ["a", "b", "c"],
        "loc": [1, 2, 3],
        "metrics": [1, 2, 3]
    })
    
    valid, coverage = validate_dataset_completeness(df, ["code", "loc", "metrics"])
    
    assert valid
    assert coverage == 1.0


def test_validate_dataset_completeness_partial():
    """Test validation with partial dataset."""
    df = pd.DataFrame({
        "code": ["a", None, "c"],
        "loc": [1, 2, 3],
        "metrics": [1, 2, 3]
    })
    
    valid, coverage = validate_dataset_completeness(df, ["code", "loc", "metrics"])
    
    assert not valid
    assert coverage == 2/3


def test_safe_json_parse_valid():
    """Test JSON parsing with valid input."""
    text = '{"key": "value"}'
    result = safe_json_parse(text)
    
    assert result == {"key": "value"}


def test_safe_json_parse_invalid():
    """Test JSON parsing with invalid input."""
    text = "not json"
    result = safe_json_parse(text, fallback={})
    
    assert result == {}


def test_calculate_statistics():
    """Test statistics calculation."""
    values = [1, 2, 3, 4, 5]
    stats = calculate_statistics(values)
    
    assert stats["mean"] == 3.0
    assert stats["min"] == 1.0
    assert stats["max"] == 5.0


def test_calculate_statistics_empty():
    """Test statistics calculation with empty list."""
    stats = calculate_statistics([])
    
    assert stats["mean"] == 0
    assert stats["std"] == 0