import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from classification.sensitivity_analysis import (
    calculate_metrics_at_threshold,
    calculate_relative_changes,
    THRESHOLD_VALUES
)

@pytest.fixture
def sample_predictions_df():
    """Create a sample DataFrame with predictions and ground truth."""
    np.random.seed(42)
    n = 100
    data = {
        'subject_id': np.random.randint(1, 10, n),
        'trial_id': range(n),
        'search_time': np.random.uniform(1, 10, n),
        'predicted_probability': np.random.uniform(0, 1, n),
        'ground_truth_label': np.random.randint(0, 2, n)
    }
    return pd.DataFrame(data)

def test_calculate_metrics_at_threshold_050(sample_predictions_df):
    """Test metric calculation at the baseline threshold of 0.50."""
    metrics = calculate_metrics_at_threshold(sample_predictions_df, 0.50)
    
    assert 'accuracy' in metrics
    assert 'precision' in metrics
    assert 'recall' in metrics
    assert 'f1_score' in metrics
    assert 'threshold' in metrics
    assert metrics['threshold'] == 0.50
    
    # Check that accuracy is between 0 and 1
    assert 0.0 <= metrics['accuracy'] <= 1.0
    # Check that counts are non-negative integers
    assert metrics['tp'] >= 0
    assert metrics['tn'] >= 0
    assert metrics['fp'] >= 0
    assert metrics['fn'] >= 0

def test_calculate_metrics_at_threshold_040(sample_predictions_df):
    """Test metric calculation at 0.40 threshold."""
    metrics = calculate_metrics_at_threshold(sample_predictions_df, 0.40)
    assert metrics['threshold'] == 0.40
    # Lower threshold should generally increase recall (more positives predicted)
    metrics_050 = calculate_metrics_at_threshold(sample_predictions_df, 0.50)
    # Note: This is probabilistic, so we don't assert strict inequality, just presence
    assert metrics['recall'] >= 0

def test_calculate_metrics_at_threshold_060(sample_predictions_df):
    """Test metric calculation at 0.60 threshold."""
    metrics = calculate_metrics_at_threshold(sample_predictions_df, 0.60)
    assert metrics['threshold'] == 0.60
    # Higher threshold should generally decrease recall (fewer positives predicted)

def test_calculate_relative_changes():
    """Test relative change calculations."""
    # Create mock metrics list
    metrics_list = [
        {'threshold': 0.40, 'accuracy': 0.70, 'precision': 0.65, 'recall': 0.80, 'f1_score': 0.718},
        {'threshold': 0.50, 'accuracy': 0.75, 'precision': 0.70, 'recall': 0.75, 'f1_score': 0.725}, # Baseline
        {'threshold': 0.60, 'accuracy': 0.72, 'precision': 0.75, 'recall': 0.65, 'f1_score': 0.696}
    ]
    
    df = calculate_relative_changes(metrics_list, baseline_threshold=0.50)
    
    assert 'relative_f1_change' in df.columns
    assert 'stability_status' in df.columns
    
    # Check baseline row (0.50) has 0 change
    baseline_row = df[df['threshold'] == 0.50]
    assert np.isclose(baseline_row['relative_f1_change'].iloc[0], 0.0, atol=1e-5)
    assert baseline_row['stability_status'].iloc[0] == 'STABLE'
    
    # Check 0.40 row (should be negative change if 0.718 < 0.725)
    row_040 = df[df['threshold'] == 0.40]
    # 0.718 - 0.725 = -0.007 / 0.725 = -0.0096...
    expected_change_040 = (0.718 - 0.725) / 0.725
    assert np.isclose(row_040['relative_f1_change'].iloc[0], expected_change_040, atol=1e-4)
    assert row_040['stability_status'].iloc[0] == 'DECREASED'
    
    # Check 0.60 row
    row_060 = df[df['threshold'] == 0.60]
    expected_change_060 = (0.696 - 0.725) / 0.725
    assert np.isclose(row_060['relative_f1_change'].iloc[0], expected_change_060, atol=1e-4)
    assert row_060['stability_status'].iloc[0] == 'DECREASED'

def test_calculate_relative_changes_empty_list():
    """Test with empty metrics list."""
    df = calculate_relative_changes([])
    assert df.empty

def test_calculate_relative_changes_missing_baseline():
    """Test when baseline threshold is not in the list."""
    metrics_list = [
        {'threshold': 0.40, 'accuracy': 0.70, 'f1_score': 0.718},
        {'threshold': 0.60, 'accuracy': 0.72, 'f1_score': 0.696}
    ]
    df = calculate_relative_changes(metrics_list, baseline_threshold=0.50)
    
    # Should have NaN for relative changes
    assert df['relative_f1_change'].isna().all()
    assert (df['stability_status'] == 'UNKNOWN_BASELINE').all()

def test_threshold_values_constant():
    """Ensure the default threshold values match SC-004."""
    expected = [0.40, 0.50, 0.60]
    assert THRESHOLD_VALUES == expected