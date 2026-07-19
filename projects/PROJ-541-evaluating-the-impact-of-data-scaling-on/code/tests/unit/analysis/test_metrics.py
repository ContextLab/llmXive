"""
Unit tests for code/analysis/metrics.py
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.metrics import calculate_confidence_interval, calculate_aggregate_metrics, run_full_analysis_pipeline

class TestConfidenceInterval:
    """Tests for the Clopper-Pearson confidence interval implementation."""

    def test_clopper_pearson_basic(self):
        """Test basic CI calculation for n=100, p=0.05 (5 successes)."""
        # n=100, successes=5 (5%)
        # Expected CI for 5/100 at 95% is approx [0.016, 0.113]
        lower, upper = calculate_confidence_interval(5, 100, alpha=0.05)
        assert 0.01 <= lower <= 0.02
        assert 0.10 <= upper <= 0.12

    def test_clopper_pearson_zero_successes(self):
        """Test CI when successes are zero."""
        lower, upper = calculate_confidence_interval(0, 100, alpha=0.05)
        assert lower == 0.0
        # Upper bound for 0/100 at 95% is approx 0.036
        assert 0.03 <= upper <= 0.04

    def test_clopper_pearson_all_successes(self):
        """Test CI when all are successes."""
        lower, upper = calculate_confidence_interval(100, 100, alpha=0.05)
        assert lower == 1.0
        # Lower bound for 100/100 at 95% is approx 0.964
        assert 0.96 <= lower <= 1.0

    def test_clopper_pearson_small_n(self):
        """Test CI with small sample size."""
        # 1/2 successes
        lower, upper = calculate_confidence_interval(1, 2, alpha=0.05)
        # For 1/2, the CI is very wide, roughly [0.01, 0.99]
        assert lower < 0.5
        assert upper > 0.5

    def test_clopper_pearson_n_zero(self):
        """Test CI when n is zero."""
        lower, upper = calculate_confidence_interval(0, 0, alpha=0.05)
        assert lower == 0.0
        assert upper == 0.0

    def test_clopper_pearson_verification_known_values(self):
        """
        Verification test against known binomial values for n=100, p=0.05.
        Expected range: low-order magnitude to a small threshold.
        """
        # For 5 successes out of 100 trials at 95% confidence:
        # The Clopper-Pearson interval is exact and should be within these bounds
        lower, upper = calculate_confidence_interval(5, 100, alpha=0.05)
        
        # Verify lower bound is a low-order magnitude (around 0.016)
        assert 0.015 <= lower <= 0.017, f"Lower bound {lower} not in expected range [0.015, 0.017]"
        
        # Verify upper bound is a small threshold (around 0.113)
        assert 0.110 <= upper <= 0.115, f"Upper bound {upper} not in expected range [0.110, 0.115]"

class TestEmpiricalErrorRate:
    """Tests for aggregate metrics calculation."""

    def test_calculate_aggregate_metrics(self):
        """Test calculation of Type I error and Power."""
        # Create mock data
        data = {
            'p_value': [0.01, 0.04, 0.06, 0.08, 0.02, 0.03, 0.9, 0.95],
            'ground_truth': ['null', 'null', 'null', 'null', 'alternative', 'alternative', 'alternative', 'alternative'],
            'scaling_method': ['std', 'std', 'std', 'std', 'std', 'std', 'minmax', 'minmax'],
            'test_type': ['t', 't', 't', 't', 't', 't', 't', 't']
        }
        df = pd.DataFrame(data)
        
        metrics = calculate_aggregate_metrics(df, alpha=0.05)
        
        assert 'empirical_error_rate' in metrics.columns
        assert 'ci_lower' in metrics.columns
        assert 'ci_upper' in metrics.columns
        
        # Check null hypothesis (Type I error)
        null_metrics = metrics[metrics['metric_type'] == 'type_i_error']
        assert not null_metrics.empty
        # 2 rejections out of 4 -> 0.5
        assert null_metrics.iloc[0]['empirical_error_rate'] == 0.5

class TestFullPipeline:
    """Tests for the full analysis pipeline."""

    def test_run_full_analysis_pipeline_with_df(self, tmp_path):
        """Test running the pipeline with a provided DataFrame."""
        # Create mock data
        data = {
            'p_value': [0.01, 0.04, 0.06, 0.08],
            'ground_truth': ['null', 'null', 'null', 'null'],
            'scaling_method': ['std', 'std', 'std', 'std'],
            'test_type': ['t', 't', 't', 't']
        }
        df = pd.DataFrame(data)
        
        # Run pipeline
        results = run_full_analysis_pipeline(df, alpha=0.05)
        
        assert 'metrics_df' in results
        assert 'metrics_path' in results
        assert 'report_path' in results
        
        # Check files exist
        assert os.path.exists(results['metrics_path'])
        assert os.path.exists(results['report_path'])

    def test_run_full_analysis_pipeline_load_path(self, tmp_path):
        """Test running the pipeline loading from a file."""
        # Create mock data file
        csv_path = tmp_path / "test_results.csv"
        data = {
            'p_value': [0.01, 0.04],
            'ground_truth': ['null', 'null'],
            'scaling_method': ['std', 'std'],
            'test_type': ['t', 't']
        }
        df = pd.DataFrame(data)
        df.to_csv(csv_path, index=False)
        
        # Run pipeline
        results = run_full_analysis_pipeline(load_path=str(csv_path))
        
        assert 'metrics_df' in results
        assert not results['metrics_df'].empty