"""
Unit tests for trend verification logic (T048).
"""
import json
import os
import tempfile
import pandas as pd
from pathlib import Path
import pytest

# Mock config for testing
import sys
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analysis.validation import verify_trend_consistency, write_trend_verification_report

@pytest.fixture
def temp_dirs():
    """Create temporary directories for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        processed_path = Path(tmpdir) / "processed"
        processed_path.mkdir()
        yield processed_path

def test_verify_trend_insufficient_solvents(temp_dirs):
    """Test verification fails when fewer than 5 solvents are present."""
    # Create minimal kinetic metrics with only 3 solvents
    metrics_data = {
        'solvent_name': ['A', 'B', 'C'],
        'lifetime_mean': [1.0, 2.0, 3.0],
        'lifetime_std': [0.1, 0.1, 0.1],
        'n_replicates': [3, 3, 3]
    }
    metrics_df = pd.DataFrame(metrics_data)
    metrics_path = temp_dirs / "kinetic_metrics.csv"
    metrics_df.to_csv(metrics_path, index=False)

    # Create dummy correlation results
    corr_data = {
        'posterior_slope': 0.5,
        'frequentist_anova_p_value': 0.01,
        'credible_intervals': {'lower': 0.1, 'upper': 0.9}
    }
    corr_path = temp_dirs / "correlation_results.json"
    with open(corr_path, 'w') as f:
        json.dump(corr_data, f)

    # Patch config paths
    with patch('analysis.validation.get_processed_data_path', return_value=temp_dirs):
        report = verify_trend_consistency(
            correlation_results_path=corr_path,
            kinetic_metrics_path=metrics_path,
            min_solvents=5
        )

    assert report['meets_minimum'] is False
    assert report['verdict'] == 'FAIL'
    assert any('Insufficient solvent conditions' in d for d in report['details'])

def test_verify_trend_significant_positive(temp_dirs):
    """Test verification passes with significant positive correlation."""
    # Create metrics with 5 solvents
    metrics_data = {
        'solvent_name': ['A', 'B', 'C', 'D', 'E'],
        'lifetime_mean': [1.0, 1.5, 2.0, 2.5, 3.0],
        'lifetime_std': [0.1, 0.1, 0.1, 0.1, 0.1],
        'n_replicates': [3, 3, 3, 3, 3]
    }
    metrics_df = pd.DataFrame(metrics_data)
    metrics_path = temp_dirs / "kinetic_metrics.csv"
    metrics_df.to_csv(metrics_path, index=False)

    # Create correlation results with significant positive slope
    corr_data = {
        'posterior_slope': 0.8,
        'frequentist_anova_p_value': 0.001,
        'credible_intervals': {'lower': 0.5, 'upper': 1.1}
    }
    corr_path = temp_dirs / "correlation_results.json"
    with open(corr_path, 'w') as f:
        json.dump(corr_data, f)

    with patch('analysis.validation.get_processed_data_path', return_value=temp_dirs):
        report = verify_trend_consistency(
            correlation_results_path=corr_path,
            kinetic_metrics_path=metrics_path,
            min_solvents=5
        )

    assert report['meets_minimum'] is True
    assert report['correlation_exists'] is True
    assert report['trend_direction'] == 'positive'
    assert report['statistical_significance'] == 'significant'
    assert report['verdict'] == 'PASS'

def test_verify_trend_not_significant(temp_dirs):
    """Test verification fails when correlation is not significant."""
    metrics_data = {
        'solvent_name': ['A', 'B', 'C', 'D', 'E'],
        'lifetime_mean': [1.0, 1.2, 1.1, 1.3, 1.2],
        'lifetime_std': [0.1, 0.1, 0.1, 0.1, 0.1],
        'n_replicates': [3, 3, 3, 3, 3]
    }
    metrics_df = pd.DataFrame(metrics_data)
    metrics_path = temp_dirs / "kinetic_metrics.csv"
    metrics_df.to_csv(metrics_path, index=False)

    # Non-significant p-value
    corr_data = {
        'posterior_slope': 0.1,
        'frequentist_anova_p_value': 0.45,
        'credible_intervals': {'lower': -0.2, 'upper': 0.4}
    }
    corr_path = temp_dirs / "correlation_results.json"
    with open(corr_path, 'w') as f:
        json.dump(corr_data, f)

    with patch('analysis.validation.get_processed_data_path', return_value=temp_dirs):
        report = verify_trend_consistency(
            correlation_results_path=corr_path,
            kinetic_metrics_path=metrics_path,
            min_solvents=5
        )

    assert report['verdict'] == 'FAIL'
    assert report['statistical_significance'] == 'not_significant'