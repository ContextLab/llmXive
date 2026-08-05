"""
Unit tests for the sensitivity analysis module.
"""
import os
import tempfile
import pandas as pd
import numpy as np
import pytest

from code.analysis.sensitivity_analysis import (
    evaluate_threshold,
    run_sensitivity_analysis,
    SensitivityResult
)
from code.utils.io_helpers import save_dataframe, load_dataframe

@pytest.fixture
def sample_metrics_df():
    """Create a synthetic dataset for testing."""
    np.random.seed(42)
    n = 100
    data = {
        'vortex_density': np.random.uniform(0.1, 0.8, n),
        'radial_variance': np.random.uniform(0.0, 1.0, n),
    }
    df = pd.DataFrame(data)
    # Create synthetic ground truth: Stable if density < 0.4
    df['ground_truth_stable'] = df['vortex_density'] < 0.4
    return df

def test_evaluate_threshold_logic():
    """Test the logic of confusion matrix calculation."""
    # Create a small, deterministic dataset
    data = {
        'vortex_density': [0.1, 0.2, 0.6, 0.7], # 2 stable (low), 2 unstable (high)
        'ground_truth_stable': [True, True, False, False] # Perfect alignment
    }
    df = pd.DataFrame(data)

    # Threshold 0.35:
    # 0.1 < 0.35 -> Pred Stable (TP)
    # 0.2 < 0.35 -> Pred Stable (TP)
    # 0.6 >= 0.35 -> Pred Unstable (TN)
    # 0.7 >= 0.35 -> Pred Unstable (TN)
    # Expected: TP=2, TN=2, FP=0, FN=0
    result = evaluate_threshold(df, metric_column='vortex_density', threshold=0.35)
    
    assert result.true_positives == 2
    assert result.true_negatives == 2
    assert result.false_positives == 0
    assert result.false_negatives == 0
    assert result.accuracy == 1.0
    assert result.precision == 1.0
    assert result.recall == 1.0

def test_evaluate_threshold_false_positives():
    """Test detection of false positives."""
    # Ground truth: All are actually unstable (False)
    # But our threshold is low, so we predict some as stable -> FP
    data = {
        'vortex_density': [0.1, 0.2, 0.6, 0.7],
        'ground_truth_stable': [False, False, False, False] # All actually unstable
    }
    df = pd.DataFrame(data)

    # Threshold 0.35:
    # 0.1 < 0.35 -> Pred Stable (FP)
    # 0.2 < 0.35 -> Pred Stable (FP)
    # 0.6 >= 0.35 -> Pred Unstable (TN)
    # 0.7 >= 0.35 -> Pred Unstable (TN)
    result = evaluate_threshold(df, metric_column='vortex_density', threshold=0.35)

    assert result.false_positives == 2
    assert result.true_negatives == 2
    assert result.true_positives == 0
    assert result.false_negatives == 0

def test_run_sensitivity_analysis_integration(sample_metrics_df):
    """Test the full pipeline with file I/O."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "metrics.csv")
        output_path = os.path.join(tmpdir, "sensitivity_report.json")

        save_dataframe(sample_metrics_df, input_path)

        results = run_sensitivity_analysis(
            input_metrics_path=input_path,
            output_path=output_path,
            thresholds=[0.25, 0.30, 0.35],
            metric_column='vortex_density',
            ground_truth_col='ground_truth_stable'
        )

        # Verify output files exist
        assert os.path.exists(output_path)
        assert os.path.exists(output_path.replace('.json', '.csv'))

        # Verify we got results for all thresholds
        assert len(results) == 3
        assert [r.threshold for r in results] == [0.25, 0.30, 0.35]

        # Verify basic statistics are non-negative
        for r in results:
            assert r.true_positives >= 0
            assert r.false_positives >= 0
            assert 0.0 <= r.f1_score <= 1.0

def test_empty_dataframe_handling():
    """Test that empty data raises appropriate error."""
    df = pd.DataFrame(columns=['vortex_density', 'ground_truth_stable'])
    with pytest.raises(ValueError, match="Input DataFrame is empty"):
        evaluate_threshold(df)