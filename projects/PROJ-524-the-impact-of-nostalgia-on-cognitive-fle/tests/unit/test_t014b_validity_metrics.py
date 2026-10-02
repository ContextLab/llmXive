"""
Unit tests for T014b validity metrics calculation.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'code'))

from task_t014b_validity_metrics import (
    load_exclusion_log,
    load_raw_count,
    calculate_validity_metrics,
    save_validity_metrics
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def raw_dataset_csv(temp_dir):
    """Create a sample raw dataset CSV."""
    csv_path = temp_dir / 'raw_dataset.csv'
    data = {
        'participant_id': ['P1', 'P2', 'P3', 'P4', 'P5'],
        'age': [70, 60, 65, 75, 80],
        'stimulus_type': ['nostalgia', 'control', 'nostalgia', 'control', 'nostalgia'],
        'perseverative_errors': [5, 10, None, 8, 6],
        'categories_completed': [3, 2, 4, 5, 3],
        'MMSE': [28, 22, 25, 27, 24]
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture
def exclusion_log_json(temp_dir):
    """Create a sample exclusion log JSON."""
    json_path = temp_dir / 'exclusion_log.json'
    data = {
        'ERR_MISSING_AGE_FIELD': 1,  # P2 is age 60
        'ERR_MISSING_SCORE': 1,      # P3 has missing perseverative_errors
        'ERR_MMSE_IMPAIRED': 1,      # P2 has MMSE 22 (< 24)
        'SIMULATION_FALLBACK': False
    }
    with open(json_path, 'w') as f:
        json.dump(data, f)
    return json_path

@pytest.fixture
def mmse_flag_json(temp_dir):
    """Create a sample MMSE flag JSON."""
    json_path = temp_dir / 'mmse_flag.json'
    data = {'has_mmse': True}
    with open(json_path, 'w') as f:
        json.dump(data, f)
    return json_path

def test_load_raw_count(raw_dataset_csv):
    """Test loading raw record count."""
    count = load_raw_count(raw_dataset_csv)
    assert count == 5

def test_load_exclusion_log(exclusion_log_json):
    """Test loading exclusion log."""
    log = load_exclusion_log(exclusion_log_json)
    assert log['ERR_MISSING_AGE_FIELD'] == 1
    assert log['ERR_MISSING_SCORE'] == 1
    assert log['ERR_MMSE_IMPAIRED'] == 1

def test_calculate_validity_metrics(raw_dataset_csv, exclusion_log_json, mmse_flag_json):
    """Test validity metrics calculation."""
    raw_count = load_raw_count(raw_dataset_csv)
    exclusion_log = load_exclusion_log(exclusion_log_json)
    
    metrics = calculate_validity_metrics(raw_count, exclusion_log, mmse_flag_json)
    
    # Total raw: 5
    # Exclusions: 1 (age) + 1 (score) + 1 (MMSE) = 3
    # Valid: 5 - 3 = 2
    # Percentage: 2/5 * 100 = 40%
    assert metrics['total_raw_records'] == 5
    assert metrics['total_exclusions'] == 3
    assert metrics['valid_records'] == 2
    assert metrics['validity_percentage'] == 40.0
    assert metrics['mmse_evaluated'] is True

def test_calculate_validity_metrics_no_mmse(temp_dir, raw_dataset_csv, exclusion_log_json):
    """Test validity metrics calculation when MMSE is not available."""
    # Create MMSE flag with has_mmse = False
    mmse_flag_path = temp_dir / 'mmse_flag.json'
    with open(mmse_flag_path, 'w') as f:
        json.dump({'has_mmse': False}, f)
    
    raw_count = load_raw_count(raw_dataset_csv)
    exclusion_log = load_exclusion_log(exclusion_log_json)
    
    metrics = calculate_validity_metrics(raw_count, exclusion_log, mmse_flag_path)
    
    # When MMSE is not available, MMSE exclusions should be ignored
    # Total exclusions: 1 (age) + 1 (score) + 0 (MMSE) = 2
    # Valid: 5 - 2 = 3
    assert metrics['total_exclusions'] == 2
    assert metrics['valid_records'] == 3
    assert metrics['mmse_evaluated'] is False

def test_save_validity_metrics(temp_dir):
    """Test saving validity metrics to JSON."""
    metrics = {
        'total_raw_records': 100,
        'total_exclusions': 20,
        'valid_records': 80,
        'validity_percentage': 80.0,
        'breakdown': {
            'age_exclusions': 10,
            'score_exclusions': 5,
            'mmse_exclusions': 5
        },
        'mmse_evaluated': True
    }
    
    output_path = temp_dir / 'validity_metrics.json'
    save_validity_metrics(metrics, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        saved_metrics = json.load(f)
    
    assert saved_metrics['validity_percentage'] == 80.0
    assert saved_metrics['valid_records'] == 80