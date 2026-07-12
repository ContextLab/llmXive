"""
Unit tests for T022a: token_reduction_verifier.py
"""
import pytest
import pandas as pd
import json
import os
import tempfile
from pathlib import Path

# Import the functions to test
from code.token_reduction_verifier import (
    load_baseline_comparison,
    calculate_reduction,
    generate_verification_report,
    THRESHOLD_PERCENT
)

@pytest.fixture
def temp_csv_dir(tmp_path):
    """Create a temporary directory structure for test data."""
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    return data_dir

def test_calculate_reduction_success(temp_csv_dir):
    """Test successful calculation of reduction."""
    # Setup data: Static=1000, Dynamic=600 -> 40% reduction
    data = {
        'condition': ['Static All-Layers', 'Dynamic'],
        'avg_tokens': [1000.0, 600.0]
    }
    df = pd.DataFrame(data)
    
    result = calculate_reduction(df)
    assert result is not None
    assert abs(result - 40.0) < 0.01

def test_calculate_reduction_below_threshold(temp_csv_dir):
    """Test calculation where reduction is below threshold (20%)."""
    # Setup data: Static=1000, Dynamic=850 -> 15% reduction
    data = {
        'condition': ['Static All-Layers', 'Dynamic'],
        'avg_tokens': [1000.0, 850.0]
    }
    df = pd.DataFrame(data)
    
    result = calculate_reduction(df)
    assert result is not None
    assert abs(result - 15.0) < 0.01

def test_calculate_reduction_missing_static(temp_csv_dir):
    """Test handling of missing Static condition."""
    data = {
        'condition': ['Dynamic'],
        'avg_tokens': [600.0]
    }
    df = pd.DataFrame(data)
    
    result = calculate_reduction(df)
    assert result is None

def test_calculate_reduction_missing_dynamic(temp_csv_dir):
    """Test handling of missing Dynamic condition."""
    data = {
        'condition': ['Static All-Layers'],
        'avg_tokens': [1000.0]
    }
    df = pd.DataFrame(data)
    
    result = calculate_reduction(df)
    assert result is None

def test_calculate_reduction_zero_static(temp_csv_dir):
    """Test handling of zero static tokens (division by zero)."""
    data = {
        'condition': ['Static All-Layers', 'Dynamic'],
        'avg_tokens': [0.0, 0.0]
    }
    df = pd.DataFrame(data)
    
    result = calculate_reduction(df)
    assert result is None

def test_generate_verification_report_pass(temp_csv_dir):
    """Test report generation for a passing case."""
    reduction = 35.0
    report = generate_verification_report(reduction)
    
    assert report['percentage_reduction'] == 35.0
    assert report['threshold_percent'] == THRESHOLD_PERCENT
    assert report['passed'] is True
    assert 'PASSED' in report['message']

def test_generate_verification_report_fail(temp_csv_dir):
    """Test report generation for a failing case."""
    reduction = 25.0
    report = generate_verification_report(reduction)
    
    assert report['percentage_reduction'] == 25.0
    assert report['passed'] is False
    assert 'FAILED' in report['message']

def test_load_baseline_comparison_missing_file(temp_csv_dir):
    """Test loading a non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_baseline_comparison(str(temp_csv_dir / "nonexistent.csv"))

def test_load_baseline_comparison_missing_columns(temp_csv_dir):
    """Test loading a file with missing required columns."""
    csv_path = temp_csv_dir / "bad.csv"
    df_bad = pd.DataFrame({'wrong_col': [1, 2]})
    df_bad.to_csv(csv_path, index=False)
    
    with pytest.raises(ValueError):
        load_baseline_comparison(str(csv_path))