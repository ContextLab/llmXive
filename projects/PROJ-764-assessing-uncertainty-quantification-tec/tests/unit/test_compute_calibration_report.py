"""
Unit tests for T024: compute_calibration_report.py

Tests the logic of loading predictions and computing metrics,
without requiring the full pipeline to run.
"""
import os
import sys
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from uq.compute_calibration_report import compute_metrics_for_method, load_predictions

@pytest.fixture
def sample_predictions():
    """Create sample predictions data."""
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'sample_id': range(n_samples),
        'method': ['deep_ensemble'] * n_samples,
        'prediction': np.random.randn(n_samples),
        'variance': np.random.rand(n_samples) * 0.5,
        'lower_50': np.random.randn(n_samples) - 0.5,
        'upper_50': np.random.randn(n_samples) + 0.5,
        'lower_90': np.random.randn(n_samples) - 1.5,
        'upper_90': np.random.randn(n_samples) + 1.5,
        'aleatoric': np.random.rand(n_samples) * 0.3,
        'epistemic': np.random.rand(n_samples) * 0.2,
        'total': np.random.rand(n_samples) * 0.5,
        'uncertainty_type': ['total'] * n_samples
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_test_data():
    """Create sample test data with ground truth."""
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'sample_id': range(n_samples),
        'formation_energy': np.random.randn(n_samples)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_input_file(sample_predictions):
    """Create a temporary input CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_predictions.to_csv(f, index=False)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_test_file(sample_test_data):
    """Create a temporary test data CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_test_data.to_csv(f, index=False)
        yield f.name
    os.unlink(f.name)

def test_load_predictions(temp_input_file):
    """Test loading predictions from CSV."""
    df = load_predictions(temp_input_file)
    assert len(df) == 100
    assert 'method' in df.columns
    assert 'prediction' in df.columns
    assert df['method'].unique()[0] == 'deep_ensemble'

def test_compute_metrics_for_method(sample_predictions, sample_test_data):
    """Test metric computation for a single method."""
    # Prepare true values
    true_values = sample_test_data.set_index('sample_id')['formation_energy']
    
    metrics = compute_metrics_for_method(sample_predictions, 'deep_ensemble', true_values)
    
    # Check that all required metrics are present
    required_keys = ['ece', 'interval_score', 'sharpness', 'coverage_50', 'coverage_90']
    for key in required_keys:
        assert key in metrics
        assert isinstance(metrics[key], float)
        assert not np.isnan(metrics[key])
    
    # Check that coverage values are between 0 and 1
    assert 0 <= metrics['coverage_50'] <= 1
    assert 0 <= metrics['coverage_90'] <= 1

def test_compute_metrics_empty_method(sample_predictions, sample_test_data):
    """Test metric computation for a non-existent method."""
    true_values = sample_test_data.set_index('sample_id')['formation_energy']
    
    metrics = compute_metrics_for_method(sample_predictions, 'non_existent_method', true_values)
    
    # Should return NaN for all metrics
    for key in ['ece', 'interval_score', 'sharpness', 'coverage_50', 'coverage_90']:
        assert np.isnan(metrics[key])

def test_load_predictions_missing_file():
    """Test loading from a non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_predictions("/non/existent/path.csv")

def test_load_predictions_missing_columns(temp_input_file):
    """Test loading with missing required columns."""
    # Load and remove a column
    df = pd.read_csv(temp_input_file)
    df = df.drop(columns=['prediction'])
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        temp_file = f.name
    
    try:
        with pytest.raises(ValueError):
            load_predictions(temp_file)
    finally:
        os.unlink(temp_file)
