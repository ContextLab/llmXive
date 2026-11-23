"""
Tests for Independent Validation Module (T038).
"""

import os
import json
import tempfile
from pathlib import Path
import numpy as np
import torch
import pytest

# Mock the module imports if necessary, or assume they are in path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.validate import (
    generate_synthetic_validation_data,
    compute_validation_metrics,
    compare_with_test_set
)
from evaluation.metrics import compute_mae, compute_r2


def test_generate_synthetic_validation_data():
    """Test that synthetic data is generated with noise."""
    base_data = {
        'spectra': np.random.rand(10, 100).astype(np.float32),
        'dipole': np.random.rand(10).astype(np.float32),
        'polarizability': np.random.rand(10).astype(np.float32),
        'homo_lumo': np.random.rand(10).astype(np.float32)
    }
    
    synthetic = generate_synthetic_validation_data(base_data, noise_std=0.1)
    
    assert 'spectra' in synthetic
    assert 'dipole' in synthetic
    assert 'polarizability' in synthetic
    assert 'homo_lumo' in synthetic
    
    # Check that noise was added
    assert not np.allclose(synthetic['spectra'], base_data['spectra'])
    assert synthetic['spectra'].shape == base_data['spectra'].shape


def test_compute_validation_metrics():
    """Test metric computation."""
    y_true = {
        'dipole': np.array([1.0, 2.0, 3.0]),
        'polarizability': np.array([4.0, 5.0, 6.0]),
        'homo_lumo': np.array([7.0, 8.0, 9.0])
    }
    y_pred = {
        'dipole': np.array([1.1, 2.1, 3.1]),
        'polarizability': np.array([4.1, 5.1, 6.1]),
        'homo_lumo': np.array([7.1, 8.1, 9.1])
    }
    
    metrics = compute_validation_metrics(y_true, y_pred)
    
    assert 'dipole' in metrics
    assert 'polarizability' in metrics
    assert 'homo_lumo' in metrics
    
    # Check MAE is small (since predictions are close)
    assert metrics['dipole']['mae'] < 0.2
    # Check R2 is high
    assert metrics['dipole']['r2'] > 0.9


def test_compare_with_test_set():
    """Test comparison logic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_metrics_path = Path(tmpdir) / "test_metrics.json"
        
        test_metrics = {
            'metrics': {
                'dipole': {'mae': 0.1, 'r2': 0.95},
                'polarizability': {'mae': 0.2, 'r2': 0.90}
            }
        }
        
        with open(test_metrics_path, 'w') as f:
            json.dump(test_metrics, f)
        
        validation_metrics = {
            'dipole': {'mae': 0.11, 'r2': 0.94}, # 10% increase, should pass
            'polarizability': {'mae': 0.30, 'r2': 0.85} # 50% increase, should fail
        }
        
        comparison = compare_with_test_set(validation_metrics, test_metrics_path)
        
        assert comparison['comparison_performed'] is True
        assert comparison['overall_status'] == 'FAIL' # Because polarizability failed
        
        assert comparison['details']['dipole']['passed'] is True
        assert comparison['details']['dipole']['relative_increase'] <= 0.20
        
        assert comparison['details']['polarizability']['passed'] is False
        assert comparison['details']['polarizability']['relative_increase'] > 0.20
