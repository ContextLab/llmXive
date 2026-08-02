"""
Unit tests for sensitivity analysis logic.
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from classification.sensitivity_analysis import (
    compute_metrics_at_threshold,
    run_sensitivity_analysis,
    THRESHOLDS_TO_SWEEP
)

@pytest.fixture
def sample_data():
    """Create sample predictions and true labels for testing."""
    np.random.seed(42)
    n_samples = 100
    
    # Generate random probabilities
    probs = np.random.rand(n_samples)
    
    # Generate binary labels (slightly correlated with prob for realism)
    true_labels = (probs > 0.5).astype(int)
    # Add some noise
    noise = np.random.rand(n_samples) > 0.8
    true_labels[noise] = 1 - true_labels[noise]
    
    df = pd.DataFrame({
        'predicted_probability': probs,
        'subject_id': [f'sub_{i%10}' for i in range(n_samples)],
        'trial_id': range(n_samples)
    })
    
    return df, pd.Series(true_labels)

def test_compute_metrics_accuracy(sample_data):
    """Test accuracy calculation."""
    df, labels = sample_data
    
    # At threshold 0.5, accuracy should be reasonable
    metrics = compute_metrics_at_threshold(df, labels, 0.5)
    
    assert 'accuracy' in metrics
    assert 0.0 <= metrics['accuracy'] <= 1.0
    assert metrics['true_positives'] >= 0
    assert metrics['true_negatives'] >= 0

def test_compute_metrics_perfect_threshold():
    """Test with a threshold that perfectly separates data."""
    df = pd.DataFrame({'predicted_probability': [0.1, 0.2, 0.8, 0.9]})
    labels = pd.Series([0, 0, 1, 1])
    
    metrics = compute_metrics_at_threshold(df, labels, 0.5)
    
    assert metrics['accuracy'] == 1.0
    assert metrics['precision'] == 1.0
    assert metrics['recall'] == 1.0
    assert metrics['f1_score'] == 1.0

def test_compute_metrics_extreme_thresholds():
    """Test with extreme thresholds."""
    df = pd.DataFrame({'predicted_probability': [0.1, 0.2, 0.8, 0.9]})
    labels = pd.Series([0, 0, 1, 1])
    
    # Threshold 0.0 -> predict all 1
    metrics_low = compute_metrics_at_threshold(df, labels, 0.0)
    assert metrics_low['recall'] == 1.0 # All positives caught
    assert metrics_low['precision'] == 0.5 # 2 TP, 2 FP
    
    # Threshold 1.0 -> predict all 0
    metrics_high = compute_metrics_at_threshold(df, labels, 1.0)
    assert metrics_high['recall'] == 0.0 # No positives caught
    assert metrics_high['precision'] == 0.0 # Division by zero handled

def test_run_sensitivity_analysis_relative_decrease(sample_data):
    """Test that relative decrease is calculated correctly."""
    df, labels = sample_data
    
    # Run analysis with a set that includes 0.50 as baseline
    thresholds = [0.40, 0.50, 0.60]
    results = run_sensitivity_analysis(df, labels, thresholds)
    
    assert 'threshold' in results.columns
    assert 'accuracy' in results.columns
    assert 'accuracy_relative_decrease' in results.columns
    
    # Check that baseline (0.50) has 0.0 relative decrease
    baseline_row = results[results['threshold'] == 0.50]
    assert len(baseline_row) == 1
    assert np.isclose(baseline_row['accuracy_relative_decrease'].values[0], 0.0)
    
    # Check that other rows have non-zero (or NaN) relative decrease
    other_rows = results[results['threshold'] != 0.50]
    for _, row in other_rows.iterrows():
        # Should be a number, not NaN unless baseline was 0 (unlikely)
        assert not pd.isna(row['accuracy_relative_decrease'])

def test_run_sensitivity_analysis_missing_baseline():
    """Test behavior when baseline threshold is not in sweep."""
    df = pd.DataFrame({'predicted_probability': [0.1, 0.2, 0.8, 0.9]})
    labels = pd.Series([0, 0, 1, 1])
    
    # Sweep without 0.50
    thresholds = [0.40, 0.60]
    results = run_sensitivity_analysis(df, labels, thresholds)
    
    # Relative decrease columns should exist but be NaN or not calculated
    # The function currently logs a warning and skips calculation
    if 'accuracy_relative_decrease' in results.columns:
        # If the column exists, it might be NaN
        assert results['accuracy_relative_decrease'].isna().all() or all(pd.isna(results['accuracy_relative_decrease']))

if __name__ == '__main__':
    pytest.main([__file__, '-v'])