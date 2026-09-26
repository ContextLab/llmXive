import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import mock_open, patch

# Add code/ to path if running from tests/
sys.path.insert(0, str(Path(__file__).parent.parent))

from classification.sensitivity_analysis import (
    load_classification_predictions,
    compute_metrics_at_threshold,
    calculate_stability_metrics,
    run_sensitivity_analysis
)

@pytest.fixture
def sample_predictions():
    """Create a small sample DataFrame for testing."""
    return pd.DataFrame({
        'true_label': [1, 1, 0, 0, 1],
        'predicted_prob': [0.8, 0.3, 0.6, 0.2, 0.9]
    })

@pytest.fixture
def temp_output_file(tmp_path):
    """Create a temporary file path."""
    return tmp_path / "test_sensitivity.csv"

def test_load_classification_predictions_valid(sample_predictions):
    """Test loading valid predictions."""
    # Mock file existence
    with patch('pathlib.Path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data=sample_predictions.to_csv(index=False))):
            df = load_classification_predictions("dummy.csv")
            assert 'true_label' in df.columns
            assert 'predicted_prob' in df.columns
            assert len(df) == 5

def test_load_classification_predictions_missing_columns(tmp_path):
    """Test loading file with missing required columns."""
    df_bad = pd.DataFrame({'other_col': [1, 2]})
    file_path = tmp_path / "bad.csv"
    df_bad.to_csv(file_path, index=False)
    
    with pytest.raises(ValueError, match="Missing required columns"):
        load_classification_predictions(str(file_path))

def test_compute_metrics_at_threshold_basic(sample_predictions):
    """Test metric computation at a specific threshold."""
    metrics = compute_metrics_at_threshold(sample_predictions, 0.5)
    
    # Expected:
    # Preds: [0.8->1, 0.3->0, 0.6->1, 0.2->0, 0.9->1]
    # Truth: [1, 1, 0, 0, 1]
    # TP: (1,1), (0,0) -> 2? No.
    # Row 0: P=1, T=1 -> TP
    # Row 1: P=0, T=1 -> FN
    # Row 2: P=1, T=0 -> FP
    # Row 3: P=0, T=0 -> TN
    # Row 4: P=1, T=1 -> TP
    # TP=2, TN=1, FP=1, FN=1
    # Acc = (2+1)/5 = 0.6
    # Prec = 2/(2+1) = 0.666
    # Rec = 2/(2+1) = 0.666
    
    assert abs(metrics['accuracy'] - 0.6) < 1e-6
    assert abs(metrics['precision'] - 0.666666) < 1e-6
    assert abs(metrics['recall'] - 0.666666) < 1e-6
    assert metrics['tp'] == 2
    assert metrics['tn'] == 1
    assert metrics['fp'] == 1
    assert metrics['fn'] == 1

def test_calculate_stability_metrics():
    """Test stability calculation logic."""
    metrics = [
        {'threshold': 0.50, 'accuracy': 0.8, 'precision': 0.8, 'recall': 0.8, 'f1_score': 0.8},
        {'threshold': 0.60, 'accuracy': 0.7, 'precision': 0.7, 'recall': 0.7, 'f1_score': 0.7}
    ]
    
    stability = calculate_stability_metrics(metrics)
    
    # Check baseline
    assert any(s['threshold'] == 0.50 and s['stability_status'] == 'BASELINE' for s in stability)
    
    # Check relative change for 0.60
    row_060 = next(s for s in stability if s['threshold'] == 0.60)
    # (0.7 - 0.8) / 0.8 = -0.125
    assert abs(row_060['rel_f1_change'] - (-0.125)) < 1e-6
    assert row_060['stability_status'] == 'DECREASE'

def test_run_sensitivity_analysis_integration(tmp_path, sample_predictions):
    """Test full pipeline execution and output file generation."""
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"
    sample_predictions.to_csv(input_file, index=False)
    
    run_sensitivity_analysis(
        input_file=str(input_file),
        output_file=str(output_file),
        thresholds=[0.40, 0.50, 0.60]
    )
    
    assert output_file.exists()
    result_df = pd.read_csv(output_file)
    assert 'threshold' in result_df.columns
    assert 'accuracy' in result_df.columns
    assert 'stability_status' in result_df.columns
    assert len(result_df) == 3  # 3 thresholds
    assert set(result_df['threshold'].values) == {0.40, 0.50, 0.60}
