"""
Unit tests for the pre-check logic (T016).

Tests verify:
- Correct calculation of normalized/raw counts
- Threshold evaluation logic
- Report generation structure
- Warning triggering when threshold not met
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

# Import the module functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from pre_check import (
    calculate_counts,
    evaluate_threshold,
    generate_report,
    NORMALIZED_THRESHOLD
)

@pytest.fixture
def sample_dataframe_normalized():
    """Create a sample DataFrame with mostly normalized data."""
    data = {
        'normalization_method': ['normalized'] * 350 + ['raw'] * 50,
        'power': [100.0] * 400,
        'wear_rate': [0.5] * 400
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_dataframe_below_threshold():
    """Create a sample DataFrame with normalized count below threshold."""
    data = {
        'normalization_method': ['normalized'] * 200 + ['raw'] * 150,
        'power': [100.0] * 350,
        'wear_rate': [0.5] * 350
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_dataframe_mixed():
    """Create a sample DataFrame with mixed normalization methods."""
    data = {
        'normalization_method': ['normalized'] * 300 + ['raw'] * 300,
        'power': [100.0] * 600,
        'wear_rate': [0.5] * 600
    }
    return pd.DataFrame(data)

def test_calculate_counts_normalized_majority(sample_dataframe_normalized):
    """Test count calculation when normalized data is majority."""
    counts = calculate_counts(sample_dataframe_normalized)
    
    assert counts['total_count'] == 400
    assert counts['normalized_count'] == 350
    assert counts['raw_count'] == 50

def test_calculate_counts_below_threshold(sample_dataframe_below_threshold):
    """Test count calculation when normalized data is below threshold."""
    counts = calculate_counts(sample_dataframe_below_threshold)
    
    assert counts['total_count'] == 350
    assert counts['normalized_count'] == 200
    assert counts['raw_count'] == 150

def test_calculate_counts_mixed(sample_dataframe_mixed):
    """Test count calculation with equal split."""
    counts = calculate_counts(sample_dataframe_mixed)
    
    assert counts['total_count'] == 600
    assert counts['normalized_count'] == 300
    assert counts['raw_count'] == 300

def test_evaluate_threshold_above_threshold(sample_dataframe_normalized):
    """Test evaluation when count is above threshold."""
    counts = calculate_counts(sample_dataframe_normalized)
    evaluation = evaluate_threshold(counts)
    
    assert evaluation['threshold'] == NORMALIZED_THRESHOLD
    assert evaluation['below_threshold'] is False
    assert evaluation['power_limitation_warning'] is None
    assert 'Proceed to Phase 4' in evaluation['recommendation']

def test_evaluate_threshold_below_threshold(sample_dataframe_below_threshold):
    """Test evaluation when count is below threshold."""
    counts = calculate_counts(sample_dataframe_below_threshold)
    evaluation = evaluate_threshold(counts)
    
    assert evaluation['threshold'] == NORMALIZED_THRESHOLD
    assert evaluation['below_threshold'] is True
    assert evaluation['power_limitation_warning'] is not None
    assert 'CRITICAL' in evaluation['power_limitation_warning']
    assert 'Acquire more normalized data' in evaluation['recommendation']

def test_evaluate_threshold_exact_boundary():
    """Test evaluation when count is exactly at threshold."""
    counts = {
        'total_count': 300,
        'normalized_count': 300,
        'raw_count': 0
    }
    evaluation = evaluate_threshold(counts)
    
    # Should NOT trigger warning when exactly at threshold
    assert evaluation['below_threshold'] is False
    assert evaluation['power_limitation_warning'] is None

def test_generate_report_structure(sample_dataframe_normalized):
    """Test that the report contains all required fields."""
    counts = calculate_counts(sample_dataframe_normalized)
    evaluation = evaluate_threshold(counts)
    report = generate_report(counts, evaluation)
    
    assert 'status' in report
    assert 'timestamp' in report
    assert 'data_source' in report
    assert 'counts' in report
    assert 'threshold_evaluation' in report
    assert 'summary' in report
    
    assert report['status'] == 'success'
    assert report['counts'] == counts
    assert report['threshold_evaluation'] == evaluation

def test_report_contains_warning_flag(sample_dataframe_below_threshold):
    """Test that report correctly reflects warning state."""
    counts = calculate_counts(sample_dataframe_below_threshold)
    evaluation = evaluate_threshold(counts)
    report = generate_report(counts, evaluation)
    
    assert 'WARNING' in report['summary']
    assert report['threshold_evaluation']['below_threshold'] is True

def test_report_contains_ok_flag(sample_dataframe_normalized):
    """Test that report correctly reflects OK state."""
    counts = calculate_counts(sample_dataframe_normalized)
    evaluation = evaluate_threshold(counts)
    report = generate_report(counts, evaluation)
    
    assert 'OK' in report['summary']
    assert report['threshold_evaluation']['below_threshold'] is False