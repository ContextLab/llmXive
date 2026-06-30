import pytest
import json
import os
import tempfile
from code.t039_log_excluded_datasets import (
    load_baseline_metrics,
    load_cleaned_metrics,
    check_missing_outcome_rate,
    log_excluded_datasets
)

@pytest.fixture
def temp_baseline_file():
    """Create a temporary baseline metrics file."""
    data = {
        'datasets': [
            {'dataset_name': 'valid_dataset', 'missing_outcome_rate': 0.1},
            {'dataset_name': 'excluded_dataset', 'missing_outcome_rate': 0.85},
            {'dataset_name': 'borderline_dataset', 'missing_outcome_rate': 0.80}
        ]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        return f.name

@pytest.fixture
def temp_cleaned_file():
    """Create a temporary cleaned metrics file."""
    data = {
        'datasets': [
            {'dataset_name': 'valid_cleaned', 'missing_outcome_rate': 0.05},
            {'dataset_name': 'excluded_cleaned', 'missing_outcome_rate': 0.90}
        ]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(data, f)
        return f.name

def test_load_baseline_metrics_valid(temp_baseline_file):
    """Test loading valid baseline metrics."""
    result = load_baseline_metrics(temp_baseline_file)
    assert len(result) == 3
    assert result[0]['dataset_name'] == 'valid_dataset'

def test_load_baseline_metrics_missing_file():
    """Test loading non-existent baseline metrics."""
    result = load_baseline_metrics('/nonexistent/path.json')
    assert result == []

def test_check_missing_outcome_rate_with_field():
    """Test missing rate calculation with explicit field."""
    dataset = {'dataset_name': 'test', 'missing_outcome_rate': 0.75}
    rate = check_missing_outcome_rate(dataset)
    assert rate == 0.75

def test_check_missing_outcome_rate_with_calculation():
    """Test missing rate calculation from missing_values."""
    dataset = {'dataset_name': 'test', 'missing_values': 80, 'total_rows': 100}
    rate = check_missing_outcome_rate(dataset)
    assert rate == 0.80

def test_check_missing_outcome_rate_default():
    """Test missing rate calculation with no data."""
    dataset = {'dataset_name': 'test'}
    rate = check_missing_outcome_rate(dataset)
    assert rate == 0.0

def test_log_excluded_datasets_identifies_high_missing(temp_baseline_file, temp_cleaned_file):
    """Test that datasets with >80% missing outcome are identified."""
    excluded = log_excluded_datasets(temp_baseline_file, temp_cleaned_file, 0.80)
    
    assert len(excluded) == 2
    dataset_names = {d['dataset_name'] for d in excluded}
    assert 'excluded_dataset' in dataset_names
    assert 'excluded_cleaned' in dataset_names

def test_log_excluded_datasets_threshold_boundary(temp_baseline_file, temp_cleaned_file):
    """Test that datasets at exactly 80% are NOT excluded."""
    excluded = log_excluded_datasets(temp_baseline_file, temp_cleaned_file, 0.80)
    
    # borderline_dataset has exactly 0.80, should not be excluded
    dataset_names = {d['dataset_name'] for d in excluded}
    assert 'borderline_dataset' not in dataset_names

def test_log_excluded_datasets_no_exclusions():
    """Test with files containing no excluded datasets."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f1:
        json.dump({'datasets': [{'dataset_name': 'good', 'missing_outcome_rate': 0.1}]}, f1)
        baseline_file = f1.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f2:
        json.dump({'datasets': [{'dataset_name': 'good_cleaned', 'missing_outcome_rate': 0.05}]}, f2)
        cleaned_file = f2.name
    
    try:
        excluded = log_excluded_datasets(baseline_file, cleaned_file, 0.80)
        assert len(excluded) == 0
    finally:
        os.unlink(baseline_file)
        os.unlink(cleaned_file)
