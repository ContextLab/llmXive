"""
Unit tests for T014b: VALIDITY METRICS
"""
import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Mock config for testing
class MockConfig:
    def __getitem__(self, key):
        if key == 'paths':
            return {
                'raw_data': tempfile.gettempdir(),
                'processed_data': tempfile.gettempdir()
            }
        return {}

# Mock the config module
import sys
from unittest.mock import patch

@pytest.fixture
def temp_files(tmp_path):
    """Create temporary test files."""
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    processed_dir.mkdir()
    
    # Create mock raw dataset
    raw_df = pd.DataFrame({
        'participant_id': ['P001', 'P002', 'P003', 'P004', 'P005'],
        'age': [70, 62, 75, 80, 65],  # P002 is < 65
        'stimulus_type': ['nostalgia', 'control', 'nostalgia', 'control', 'nostalgia'],
        'perseverative_errors': [5.0, 10.0, None, 8.0, 6.0],  # P003 is null
        'categories_completed': [4.0, 3.0, 5.0, None, 4.0],  # P004 is null
        'MMSE': [28, 26, 22, 25, 27]  # P003 is < 24
    })
    raw_path = raw_dir / "raw_dataset.csv"
    raw_df.to_csv(raw_path, index=False)
    
    # Create mock exclusion log
    exclusion_log = {
        'ERR_MISSING_AGE_FIELD': 1,  # P002
        'ERR_MISSING_SCORE': 2,      # P003 (errors), P004 (categories)
        'ERR_MMSE_IMPAIRED': 1,      # P003
        'SIMULATION_FALLBACK': False
    }
    exclusion_path = processed_dir / "exclusion_log.json"
    with open(exclusion_path, 'w') as f:
        json.dump(exclusion_log, f)
    
    # Create mock mmse_flag
    mmse_flag = {'has_mmse': True}
    mmse_path = processed_dir / "mmse_flag.json"
    with open(mmse_path, 'w') as f:
        json.dump(mmse_flag, f)
    
    return {
        'raw_path': raw_path,
        'processed_dir': processed_dir,
        'exclusion_path': exclusion_path,
        'mmse_path': mmse_path
    }

def test_load_raw_count(temp_files):
    """Test loading raw record count."""
    from code.task_t014b_validity_metrics import load_raw_count, get_config_paths
    
    paths = {
        'raw_dataset': temp_files['raw_path'],
        'processed_dir': temp_files['processed_dir'],
        'validity_metrics': temp_files['processed_dir'] / 'validity_metrics.json',
        'exclusion_log': temp_files['exclusion_path']
    }
    
    count = load_raw_count(paths)
    assert count == 5

def test_calculate_validity_metrics_basic():
    """Test validity metrics calculation."""
    from code.task_t014b_validity_metrics import calculate_validity_metrics
    
    total_records = 100
    exclusion_log = {
        'ERR_MISSING_AGE_FIELD': 10,
        'ERR_MISSING_SCORE': 5,
        'ERR_MMSE_IMPAIRED': 3,
        'SIMULATION_FALLBACK': False
    }
    
    metrics = calculate_validity_metrics(total_records, exclusion_log, has_mmse=True)
    
    assert metrics['total_raw_records'] == 100
    assert metrics['age_excluded'] == 10
    assert metrics['score_excluded'] == 5
    assert metrics['mmse_excluded'] == 3
    assert metrics['total_excluded'] == 18
    assert metrics['valid_records'] == 82
    assert metrics['validity_percentage'] == 82.0
    assert metrics['has_mmse_available'] == True

def test_calculate_validity_metrics_zero_total():
    """Test validity metrics calculation with zero total records."""
    from code.task_t014b_validity_metrics import calculate_validity_metrics
    
    total_records = 0
    exclusion_log = {
        'ERR_MISSING_AGE_FIELD': 0,
        'ERR_MISSING_SCORE': 0,
        'ERR_MMSE_IMPAIRED': 0,
        'SIMULATION_FALLBACK': False
    }
    
    metrics = calculate_validity_metrics(total_records, exclusion_log, has_mmse=True)
    
    assert metrics['valid_records'] == 0
    assert metrics['validity_percentage'] == 0.0

def test_save_validity_metrics(temp_files):
    """Test saving validity metrics to file."""
    from code.task_t014b_validity_metrics import save_validity_metrics
    
    metrics = {
        'total_raw_records': 100,
        'validity_percentage': 85.5
    }
    output_path = temp_files['processed_dir'] / 'test_metrics.json'
    
    save_validity_metrics(metrics, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        saved = json.load(f)
    assert saved['total_raw_records'] == 100
    assert saved['validity_percentage'] == 85.5