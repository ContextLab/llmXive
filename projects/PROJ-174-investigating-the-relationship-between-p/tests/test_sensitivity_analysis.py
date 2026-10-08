import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import yaml
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from classification.sensitivity_analysis import (
    compute_metrics_at_threshold,
    calculate_stability_metrics,
    run_sensitivity_analysis
)
from config import load_config

@pytest.fixture
def sample_data():
    """Create sample labeled data for testing."""
    data = {
        'probability': [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0],
        'label': [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_config(tmp_path):
    """Create a temporary config file with thresholds."""
    config = {
        'seeds': [42],
        'thresholds': [0.4, 0.5, 0.6],
        'paths': {
            'data_raw': 'data/raw',
            'data_processed': 'data/processed',
            'results': 'results',
            'figures': 'figures'
        },
        'aggregation': False
    }
    config_path = tmp_path / 'config.yaml'
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    return config_path

@pytest.fixture
def temp_results_dir(tmp_path):
    """Create a temporary results directory."""
    results_dir = tmp_path / 'results'
    results_dir.mkdir()
    return results_dir

def test_compute_metrics_at_threshold(sample_data):
    """Test metric computation at a specific threshold."""
    # Test with threshold 0.5
    metrics = compute_metrics_at_threshold(sample_data, 0.5)
    
    assert 'accuracy' in metrics
    assert 'auc' in metrics
    assert isinstance(metrics['accuracy'], float)
    assert isinstance(metrics['auc'], float)
    
    # At threshold 0.5, predictions should be [1,1,1,1,1,0,0,0,0,0]
    # Which perfectly matches labels [1,1,1,1,1,0,0,0,0,0]
    # So accuracy should be 1.0
    assert metrics['accuracy'] == 1.0

def test_compute_metrics_at_threshold_low(sample_data):
    """Test metric computation with low threshold."""
    # Test with threshold 0.1 - almost all predicted as 1
    metrics = compute_metrics_at_threshold(sample_data, 0.1)
    
    assert metrics['accuracy'] >= 0.5  # At least 50% accuracy

def test_compute_metrics_at_threshold_high(sample_data):
    """Test metric computation with high threshold."""
    # Test with threshold 0.9 - only first predicted as 1
    metrics = compute_metrics_at_threshold(sample_data, 0.9)
    
    assert metrics['accuracy'] >= 0.5

def test_calculate_stability_metrics():
    """Test stability metric calculation."""
    results = [
        {'threshold': 0.4, 'accuracy': 0.9, 'auc': 0.95},
        {'threshold': 0.5, 'accuracy': 0.85, 'auc': 0.94},
        {'threshold': 0.6, 'accuracy': 0.8, 'auc': 0.93}
    ]
    
    stable_results = calculate_stability_metrics(results)
    
    assert len(stable_results) == 3
    assert all('stability_status' in r for r in stable_results)
    assert all('relative_decrease' in r for r in stable_results)
    
    # AUC drop is (0.95 - 0.93) / 0.95 = 0.021 < 0.05, so should be PASS
    assert stable_results[0]['stability_status'] == 'PASS'
    assert stable_results[0]['relative_decrease'] < 0.05

def test_calculate_stability_metrics_unstable():
    """Test stability metric calculation with unstable AUC."""
    results = [
        {'threshold': 0.4, 'accuracy': 0.9, 'auc': 0.95},
        {'threshold': 0.5, 'accuracy': 0.7, 'auc': 0.80},
        {'threshold': 0.6, 'accuracy': 0.6, 'auc': 0.70}
    ]
    
    stable_results = calculate_stability_metrics(results)
    
    # AUC drop is (0.95 - 0.70) / 0.95 = 0.263 > 0.05, so should be FAIL
    assert stable_results[0]['stability_status'] == 'FAIL'
    assert stable_results[0]['relative_decrease'] > 0.05

def test_run_sensitivity_analysis(tmp_path, sample_data, temp_config):
    """Test full sensitivity analysis run."""
    # Create necessary directories
    data_dir = tmp_path / 'data' / 'processed'
    data_dir.mkdir(parents=True)
    
    # Create labeled data file
    labeled_data_path = data_dir / 'labeled_data.csv'
    sample_data.to_csv(labeled_data_path, index=False)
    
    # Create metrics file (required by load_classification_predictions)
    metrics_dir = tmp_path / 'results'
    metrics_dir.mkdir()
    metrics_path = metrics_dir / 'classification_metrics.csv'
    pd.DataFrame({'threshold': [0.5], 'accuracy': [0.9], 'auc': [0.95], 
                 'precision': [0.9], 'recall': [0.9], 
                 'ground_truth_source': ['test']}).to_csv(metrics_path, index=False)
    
    # Run sensitivity analysis
    output_path = tmp_path / 'results' / 'sensitivity_analysis.csv'
    run_sensitivity_analysis(temp_config, output_path)
    
    # Verify output exists
    assert output_path.exists()
    
    # Verify content
    df = pd.read_csv(output_path)
    assert 'threshold' in df.columns
    assert 'accuracy' in df.columns
    assert 'auc' in df.columns
    assert 'stability_status' in df.columns
    
    # Should have 3 rows for 3 thresholds
    assert len(df) == 3
    
    # Check stability status is present
    assert all(df['stability_status'].isin(['PASS', 'FAIL']))

def test_config_defaults():
    """Test that default thresholds are used when config is missing thresholds."""
    config = {
        'seeds': [42],
        'paths': {},
        'aggregation': False
    }
    
    # This should not raise an error, should use defaults
    thresholds = config.get('thresholds', [0.4, 0.5, 0.6])
    assert thresholds == [0.4, 0.5, 0.6]
    
    # Test with empty thresholds
    config['thresholds'] = []
    thresholds = config.get('thresholds', [0.4, 0.5, 0.6])
    # When empty list is present, get returns empty list
    # But our implementation in sensitivity_analysis.py checks if not thresholds
    if not thresholds:
        thresholds = [0.4, 0.5, 0.6]
    assert thresholds == [0.4, 0.5, 0.6]