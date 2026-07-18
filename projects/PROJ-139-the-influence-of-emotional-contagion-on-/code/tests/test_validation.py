"""
Tests for the validation module.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from code.data.validation import (
    check_ground_truth_availability,
    classify_thread,
    validate_and_classify,
    generate_failure_report
)

@pytest.fixture
def sample_valid_thread():
    """Create a sample thread with valid ground truth."""
    return pd.Series({
        'thread_id': 'test_001',
        'ground_truth_label': 1,
        'ground_truth_source': 'external_expert',
        'other_column': 'value'
    })

@pytest.fixture
def sample_invalid_thread_missing_label():
    """Create a sample thread with missing ground truth label."""
    return pd.Series({
        'thread_id': 'test_002',
        'ground_truth_label': np.nan,
        'ground_truth_source': 'external_expert',
        'other_column': 'value'
    })

@pytest.fixture
def sample_invalid_thread_missing_source():
    """Create a sample thread with missing ground truth source."""
    return pd.Series({
        'thread_id': 'test_003',
        'ground_truth_label': 0,
        'ground_truth_source': np.nan,
        'other_column': 'value'
    })

@pytest.fixture
def sample_thread_missing_columns():
    """Create a sample thread missing ground truth columns."""
    return pd.Series({
        'thread_id': 'test_004',
        'other_column': 'value'
    })

def test_check_ground_truth_valid(sample_valid_thread):
    """Test that a thread with valid ground truth is accepted."""
    has_gt, reason = check_ground_truth_availability(sample_valid_thread)
    assert has_gt is True
    assert reason is None

def test_check_ground_truth_missing_label(sample_invalid_thread_missing_label):
    """Test that a thread with missing label is rejected."""
    has_gt, reason = check_ground_truth_availability(sample_invalid_thread_missing_label)
    assert has_gt is False
    assert reason == "MISSING_LABEL"

def test_check_ground_truth_missing_source(sample_invalid_thread_missing_source):
    """Test that a thread with missing source is rejected."""
    has_gt, reason = check_ground_truth_availability(sample_invalid_thread_missing_source)
    assert has_gt is False
    assert reason == "MISSING_SOURCE"

def test_check_ground_truth_missing_columns(sample_thread_missing_columns):
    """Test that a thread with missing columns is rejected."""
    has_gt, reason = check_ground_truth_availability(sample_thread_missing_columns)
    assert has_gt is False
    assert reason == "MISSING_COLUMNS"

def test_classify_thread_valid(sample_valid_thread):
    """Test classification of a valid thread."""
    result = classify_thread(sample_valid_thread)
    assert result['status'] == 'valid'
    assert result['ground_truth_available'] is True
    assert result['exclusion_reason'] is None

def test_classify_thread_invalid(sample_invalid_thread_missing_label):
    """Test classification of an invalid thread."""
    result = classify_thread(sample_invalid_thread_missing_label)
    assert result['status'] == 'excluded'
    assert result['ground_truth_available'] is False
    assert result['exclusion_reason'] == "MISSING_LABEL"

def test_validate_and_classify():
    """Test the full validation and classification process."""
    # Create sample data
    data = {
        'thread_id': ['t1', 't2', 't3', 't4'],
        'ground_truth_label': [1, np.nan, 0, None],
        'ground_truth_source': ['src1', 'src2', np.nan, 'src4'],
        'value': [10, 20, 30, 40]
    }
    df = pd.DataFrame(data)
    
    # Run validation
    validated_df, stats = validate_and_classify(df)
    
    # Check results
    assert len(validated_df) == 4
    assert stats['total'] == 4
    assert stats['valid'] == 1  # Only t1 is valid
    assert stats['excluded'] == 3
    assert stats['valid_percentage'] == 25.0
    
    # Check that status column exists
    assert 'status' in validated_df.columns
    assert validated_df['status'].iloc[0] == 'valid'
    assert validated_df['status'].iloc[1] == 'excluded'
    assert validated_df['status'].iloc[2] == 'excluded'
    assert validated_df['status'].iloc[3] == 'excluded'

def test_generate_failure_report_above_threshold(tmp_path):
    """Test that no report is generated when threshold is met."""
    stats = {
        'valid': 50,
        'excluded': 10,
        'total': 60,
        'valid_percentage': 83.33,
        'excluded_percentage': 16.67
    }
    
    output_path = tmp_path / "failure_report.json"
    generate_failure_report(stats, output_path)
    
    # No report should be generated
    assert not output_path.exists()

def test_generate_failure_report_below_threshold(tmp_path):
    """Test that a report is generated when threshold is not met."""
    stats = {
        'valid': 10,
        'excluded': 90,
        'total': 100,
        'valid_percentage': 10.0,
        'excluded_percentage': 90.0
    }
    
    output_path = tmp_path / "failure_report.json"
    generate_failure_report(stats, output_path)
    
    # Report should be generated
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    assert report['status'] == 'FAILURE'
    assert report['valid_percentage'] == 10.0
    assert 'below required threshold' in report['reason']

def test_generate_failure_report_exactly_at_threshold(tmp_path):
    """Test behavior when exactly at threshold."""
    stats = {
        'valid': 30,
        'excluded': 70,
        'total': 100,
        'valid_percentage': 30.0,
        'excluded_percentage': 70.0
    }
    
    output_path = tmp_path / "failure_report.json"
    generate_failure_report(stats, output_path)
    
    # No report should be generated (30% meets the >= 30% threshold)
    assert not output_path.exists()
