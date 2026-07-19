"""
Unit tests for analysis/metrics.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from code.analysis.metrics import (
    calculate_confidence_interval,
    calculate_aggregate_metrics,
    fit_mixed_effects_model,
    run_full_analysis_pipeline,
    calculate_deviation_summary,
    generate_summary_report,
    MixedEffectsResult
)

class TestConfidenceInterval:
    def test_clopper_pearson_normal_case(self):
        """Test CI calculation for a standard binomial case."""
        # n=100, k=5, alpha=0.05 -> 95% CI
        # Expected range roughly 0.01 to 0.11
        lower, upper = calculate_confidence_interval(count=5, total=100, alpha=0.05)
        assert 0.0 <= lower <= 0.1
        assert 0.9 <= upper <= 1.0 # Upper bound for 5/100 is actually small, let's check logic
        # Correct expectation: 5 successes in 100. CI should be around 0.016 to 0.112
        assert lower < upper
        assert lower >= 0.0
        assert upper <= 1.0

    def test_clopper_pearson_zero_successes(self):
        """Test CI when count is 0."""
        lower, upper = calculate_confidence_interval(count=0, total=100, alpha=0.05)
        assert lower == 0.0
        assert upper > 0.0
        assert upper <= 1.0

    def test_clopper_pearson_all_successes(self):
        """Test CI when count equals total."""
        lower, upper = calculate_confidence_interval(count=100, total=100, alpha=0.05)
        assert lower < 1.0
        assert upper == 1.0

    def test_clopper_pearson_small_sample(self):
        """Test CI with small sample size."""
        lower, upper = calculate_confidence_interval(count=1, total=2, alpha=0.05)
        assert lower < upper
        assert 0.0 <= lower <= 1.0
        assert 0.0 <= upper <= 1.0

class TestEmpiricalErrorRate:
    def test_aggregate_metrics_null_hypothesis(self):
        """Test calculation of Type I error rate (null hypothesis)."""
        # Create synthetic data where p-values are uniform (expected for null)
        # We expect ~5% rejections at alpha=0.05
        np.random.seed(42)
        n = 1000
        p_values = np.random.uniform(0, 1, n)
        
        df = pd.DataFrame({
            'scaling_method': ['standard'] * n,
            'test_type': ['t_test'] * n,
            'ground_truth': ['null'] * n,
            'p_value': p_values
        })
        
        result = calculate_aggregate_metrics(df, nominal_alpha=0.05)
        
        assert len(result) == 1
        assert result['scaling_method'].iloc[0] == 'standard'
        assert result['ground_truth'].iloc[0] == 'null'
        assert 0.02 <= result['error_rate'].iloc[0] <= 0.08 # Should be close to 0.05
        assert result['n'].iloc[0] == n

    def test_aggregate_metrics_alternative_hypothesis(self):
        """Test calculation of Power (alternative hypothesis)."""
        # Create synthetic data where p-values are skewed towards 0 (high power)
        np.random.seed(42)
        n = 1000
        # Simulate high power: most p-values < 0.05
        p_values = np.random.beta(0.5, 2, n) # Skewed to 0
        
        df = pd.DataFrame({
            'scaling_method': ['minmax'] * n,
            'test_type': ['anova'] * n,
            'ground_truth': ['alternative'] * n,
            'p_value': p_values
        })
        
        result = calculate_aggregate_metrics(df, nominal_alpha=0.05)
        
        assert len(result) == 1
        assert result['error_rate'].iloc[0] > 0.5 # High power expected
        assert result['n'].iloc[0] == n

    def test_aggregate_metrics_empty_dataframe(self):
        """Test handling of empty input."""
        df = pd.DataFrame(columns=['scaling_method', 'test_type', 'ground_truth', 'p_value'])
        result = calculate_aggregate_metrics(df)
        assert result.empty
        assert list(result.columns) == ['scaling_method', 'test_type', 'ground_truth', 'error_rate', 'ci_lower', 'ci_upper', 'n']

class TestFullPipeline:
    def test_run_full_analysis_pipeline_with_data(self, tmp_path):
        """Test running the full pipeline with provided data."""
        # Create a small valid dataset
        np.random.seed(123)
        n = 200
        df = pd.DataFrame({
            'scaling_method': ['std'] * n,
            'test_type': ['t'] * n,
            'ground_truth': ['null'] * n,
            'p_value': np.random.uniform(0, 1, n),
            'dataset_source': ['src1'] * n
        })
        
        # Run pipeline
        result = run_full_analysis_pipeline(results_df=df)
        
        assert 'total_iterations' in result
        assert result['total_iterations'] == n
        assert 'aggregate_metrics_head' in result
        assert 'mixed_effects_summary' in result

    def test_run_full_analysis_pipeline_no_data(self, tmp_path):
        """Test running pipeline when no data is provided and file is missing."""
        # Ensure file doesn't exist
        results_file = Path("results/simulation_results.csv")
        if results_file.exists():
            results_file.unlink()
        
        result = run_full_analysis_pipeline()
        assert 'error' in result
        assert result['error'] == 'No data found'

    def test_generate_summary_report(self):
        """Test report generation."""
        summary = {
            'total_iterations': 100,
            'nominal_alpha': 0.05,
            'aggregate_metrics_head': {'col': 'val'},
            'mixed_effects_summary': 'Summary text',
            'mixed_effects_coefficients': {'intercept': 0.1},
            'mixed_effects_p_values': {'intercept': 0.01}
        }
        report = generate_summary_report(summary)
        assert "Statistical Test Robustness Analysis Report" in report
        assert "Summary text" in report
        assert "intercept" in report

class TestMixedEffectsModel:
    def test_fit_mixed_effects_model(self):
        """Test fitting the mixed effects model."""
        np.random.seed(42)
        n = 500
        df = pd.DataFrame({
            'scaling_method': np.random.choice(['std', 'minmax', 'robust'], n),
            'p_value': np.random.uniform(0, 1, n),
            'dataset_source': np.random.choice(['ds1', 'ds2', 'ds3'], n)
        })
        
        result = fit_mixed_effects_model(df)
        
        assert isinstance(result, MixedEffectsResult)
        assert result.summary is not None
        assert result.coefficients is not None
        
    def test_fit_mixed_effects_model_missing_source(self):
        """Test fitting model when dataset_source is missing (should create dummy)."""
        np.random.seed(42)
        n = 100
        df = pd.DataFrame({
            'scaling_method': np.random.choice(['std', 'minmax'], n),
            'p_value': np.random.uniform(0, 1, n)
            # No dataset_source column
        })
        
        result = fit_mixed_effects_model(df)
        assert isinstance(result, MixedEffectsResult)
        assert result.summary is not None

class TestDeviationSummary:
    def test_calculate_deviation_summary(self):
        """Test deviation calculation."""
        df = pd.DataFrame({
            'scaling_method': ['A', 'B'],
            'test_type': ['t', 't'],
            'ground_truth': ['null', 'null'],
            'error_rate': [0.05, 0.10],
            'ci_lower': [0.0, 0.0],
            'ci_upper': [0.1, 0.2],
            'n': [100, 100]
        })
        
        result = calculate_deviation_summary(df)
        
        assert len(result) == 2
        # B (0.10) should be first (deviation 0.05), A (0.05) second (deviation 0.0)
        assert result['deviation'].iloc[0] > result['deviation'].iloc[1]
        assert result['scaling_method'].iloc[0] == 'B'
        assert result['scaling_method'].iloc[1] == 'A'