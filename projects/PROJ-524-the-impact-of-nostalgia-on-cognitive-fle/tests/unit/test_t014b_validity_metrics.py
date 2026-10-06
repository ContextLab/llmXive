"""
Unit tests for T014b: Validity Metrics
"""
import os
import json
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to test
from task_t014b_validity_metrics import (
    get_config_paths,
    load_raw_count,
    load_exclusion_log,
    calculate_validity_metrics,
    save_validity_metrics
)

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    data_raw = tmp_path / "data" / "raw"
    data_processed = tmp_path / "data" / "processed"
    data_raw.mkdir(parents=True)
    data_processed.mkdir(parents=True)
    return {
        'raw': data_raw,
        'processed': data_processed,
        'tmp': tmp_path
    }

@pytest.fixture
def mock_config(temp_dir):
    """Mock config with test paths."""
    return {
        'paths': {
            'data_raw': str(temp_dir['raw']),
            'data_processed': str(temp_dir['processed']),
            'root': str(temp_dir['tmp'])
        }
    }

def test_get_config_paths(mock_config):
    """Test that get_config_paths returns correct paths."""
    with patch('task_t014b_validity_metrics.get_config', return_value=mock_config):
        paths = get_config_paths()
        
        assert 'raw_dataset' in paths
        assert 'exclusion_log' in paths
        assert 'output_file' in paths
        assert 'mmse_flag' in paths
        
        assert paths['raw_dataset'].endswith('raw_dataset.csv')
        assert paths['exclusion_log'].endswith('exclusion_log.json')
        assert paths['output_file'].endswith('validity_metrics.json')
        assert paths['mmse_flag'].endswith('mmse_flag.json')

def test_load_raw_count(temp_dir, mock_config):
    """Test loading raw dataset count."""
    # Create a test CSV
    test_df = pd.DataFrame({
        'participant_id': range(10),
        'age': [70 + i for i in range(10)],
        'stimulus_type': ['nostalgia'] * 5 + ['control'] * 5
    })
    csv_path = temp_dir['raw'] / 'raw_dataset.csv'
    test_df.to_csv(csv_path, index=False)
    
    with patch('task_t014b_validity_metrics.get_config', return_value=mock_config):
        paths = get_config_paths()
        count = load_raw_count(paths)
        
        assert count == 10

def test_load_raw_count_missing_file(temp_dir, mock_config):
    """Test error handling when raw dataset is missing."""
    with patch('task_t014b_validity_metrics.get_config', return_value=mock_config):
        paths = get_config_paths()
        
        with pytest.raises(FileNotFoundError):
            load_raw_count(paths)

def test_load_exclusion_log(temp_dir, mock_config):
    """Test loading exclusion log."""
    exclusion_data = {
        'ERR_MISSING_AGE_FIELD': 5,
        'ERR_MISSING_SCORE': 3,
        'ERR_MMSE_IMPAIRED': 2,
        'SIMULATION_FALLBACK': False
    }
    json_path = temp_dir['processed'] / 'exclusion_log.json'
    with open(json_path, 'w') as f:
        json.dump(exclusion_data, f)
    
    with patch('task_t014b_validity_metrics.get_config', return_value=mock_config):
        paths = get_config_paths()
        log_data = load_exclusion_log(paths)
        
        assert log_data['ERR_MISSING_AGE_FIELD'] == 5
        assert log_data['ERR_MISSING_SCORE'] == 3
        assert log_data['ERR_MMSE_IMPAIRED'] == 2

def test_calculate_validity_metrics():
    """Test validity metrics calculation."""
    total_raw = 100
    exclusion_log = {
        'ERR_MISSING_AGE_FIELD': 10,
        'ERR_MISSING_SCORE': 5,
        'ERR_MMSE_IMPAIRED': 3,
        'SIMULATION_FALLBACK': False
    }
    
    metrics = calculate_validity_metrics(total_raw, exclusion_log, '/fake/path.json')
    
    assert metrics['total_raw_records'] == 100
    assert metrics['valid_records'] == 82  # 100 - 10 - 5 - 3
    assert metrics['total_exclusions'] == 18
    assert metrics['validity_percentage'] == 82.0
    assert metrics['exclusion_breakdown']['ERR_MISSING_AGE_FIELD'] == 10

def test_calculate_validity_metrics_with_mmse(temp_dir):
    """Test validity metrics when MMSE is available."""
    total_raw = 100
    exclusion_log = {
        'ERR_MISSING_AGE_FIELD': 10,
        'ERR_MISSING_SCORE': 5,
        'ERR_MMSE_IMPAIRED': 3,
        'SIMULATION_FALLBACK': False
    }
    
    # Create MMSE flag file
    mmse_flag = {'has_mmse': True}
    mmse_path = temp_dir / 'mmse_flag.json'
    with open(mmse_path, 'w') as f:
        json.dump(mmse_flag, f)
    
    metrics = calculate_validity_metrics(total_raw, exclusion_log, str(mmse_path))
    
    assert metrics['mmse_available_for_exclusion'] is True
    assert metrics['validity_percentage'] == 82.0

def test_calculate_validity_metrics_zero_raw():
    """Test edge case with zero raw records."""
    exclusion_log = {
        'ERR_MISSING_AGE_FIELD': 0,
        'ERR_MISSING_SCORE': 0,
        'ERR_MMSE_IMPAIRED': 0
    }
    
    metrics = calculate_validity_metrics(0, exclusion_log, '/fake/path.json')
    
    assert metrics['total_raw_records'] == 0
    assert metrics['valid_records'] == 0
    assert metrics['validity_percentage'] == 0.0

def test_save_validity_metrics(temp_dir):
    """Test saving validity metrics."""
    metrics = {
        'timestamp': '2024-01-01T00:00:00',
        'total_raw_records': 100,
        'valid_records': 82,
        'validity_percentage': 82.0
    }
    output_path = temp_dir / 'validity_metrics.json'
    
    save_validity_metrics(metrics, str(output_path))
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
    
    assert saved_data['total_raw_records'] == 100
    assert saved_data['validity_percentage'] == 82.0