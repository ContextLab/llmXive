import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os
import tempfile
import json
from scipy import stats

# Add project root to path for imports if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.metrics import (
    calculate_aggregate_metrics, 
    fit_real_world_mixed_effects_model,
    calculate_deviation_summary,
    calculate_confidence_interval
)

class TestMixedEffectsRealWorld:
    """Test T031b: Mixed-effects model for real-world data."""

    def test_fit_real_world_mixed_effects_model(self, tmp_path):
        """Verify that the model fits and saves the CSV."""
        # Create a mock dataset mimicking real-world results
        data = {
            'scaling_method': ['standard', 'minmax', 'robust', 'standard', 'minmax', 'robust'],
            'dataset_id': ['iris', 'iris', 'iris', 'wine', 'wine', 'wine'],
            'deviation': [0.01, -0.02, 0.005, 0.02, -0.01, 0.01]
        }
        df = pd.DataFrame(data)
        
        # Ensure results directory exists for the side effect of saving
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        try:
            model, summary = fit_real_world_mixed_effects_model(df)
            
            # Check return types
            assert model is not None
            assert isinstance(summary, str)
            assert len(summary) > 0
            
            # Check that the CSV was created
            csv_path = Path("results/mixed_effects_summary.csv")
            assert csv_path.exists(), "Output CSV file was not created."
            
            # Verify CSV content
            saved_df = pd.read_csv(csv_path)
            assert 'term' in saved_df.columns
            assert 'estimate' in saved_df.columns
            assert 'p_value' in saved_df.columns
            
            # Basic sanity check on coefficients
            assert not saved_df['estimate'].isna().all()
            
        finally:
            # Cleanup
            if csv_path.exists():
                csv_path.unlink()

    def test_empty_dataframe_raises(self):
        """Verify that an empty DataFrame raises an error."""
        empty_df = pd.DataFrame(columns=['scaling_method', 'dataset_id', 'deviation'])
        with pytest.raises(ValueError, match="Input DataFrame is empty"):
            fit_real_world_mixed_effects_model(empty_df)

    def test_invalid_formula_handling(self):
        """Verify handling of missing required columns."""
        df = pd.DataFrame({
            'scaling_method': ['standard'],
            'dataset_id': ['iris']
            # Missing 'deviation' column
        })
        with pytest.raises(Exception):
            fit_real_world_mixed_effects_model(df)

class TestEmpiricalErrorRate:
    """Test T025: Contract test for empirical error rate calculation."""

    def test_error_rate_calculation(self):
        """Verify error rate is count < alpha / total."""
        p_values = [0.01, 0.02, 0.06, 0.07, 0.04] # 3 rejections at alpha=0.05
        alpha = 0.05
        result = calculate_aggregate_metrics(p_values, alpha)
        
        assert result['n'] == 5
        assert result['rejections'] == 3
        assert abs(result['error_rate'] - 0.6) < 1e-6

    def test_empty_list(self):
        """Verify behavior with empty list."""
        result = calculate_aggregate_metrics([], 0.05)
        assert result['error_rate'] == 0.0
        assert result['n'] == 0

class TestConfidenceInterval:
    """Test T026b: Verification Test for Clopper-Pearson implementation."""

    def test_clopper_pearson_known_values_n100_p05(self):
        """
        Verify the Clopper-Pearson implementation against known binomial values.
        Scenario: n=100, observed successes k=5 (p=0.05).
        Expected: The 95% CI lower bound should be a low-order magnitude (e.g. ~0.006)
        and the upper bound should be a small threshold (e.g. ~0.107).
        """
        n = 100
        k = 5
        alpha = 0.05  # 95% CI
        
        lower, upper = calculate_confidence_interval(k, n, alpha)
        
        # Validate types
        assert isinstance(lower, float)
        assert isinstance(upper, float)
        
        # Validate range: 0 <= lower <= k/n <= upper <= 1
        assert 0.0 <= lower <= k/n
        assert k/n <= upper <= 1.0
        
        # Validate against known statistical bounds for n=100, k=5, 95% CI
        # Using scipy.stats.beta.ppf for Clopper-Pearson exact calculation:
        # Lower: beta.ppf(alpha/2, k, n-k+1)
        # Upper: beta.ppf(1 - alpha/2, k+1, n-k)
        expected_lower = stats.beta.ppf(alpha/2, k, n-k+1)
        expected_upper = stats.beta.ppf(1 - alpha/2, k+1, n-k)
        
        # Allow for minor floating point differences, but strict on order of magnitude
        assert abs(lower - expected_lower) < 1e-6, f"Lower bound mismatch: {lower} vs {expected_lower}"
        assert abs(upper - expected_upper) < 1e-6, f"Upper bound mismatch: {upper} vs {expected_upper}"

    def test_clopper_pearson_zero_successes(self):
        """Test CI when k=0."""
        n = 100
        k = 0
        alpha = 0.05
        
        lower, upper = calculate_confidence_interval(k, n, alpha)
        
        assert lower == 0.0
        # Upper bound should be small but non-zero
        assert 0.0 < upper < 0.05

    def test_clopper_pearson_all_successes(self):
        """Test CI when k=n."""
        n = 100
        k = 100
        alpha = 0.05
        
        lower, upper = calculate_confidence_interval(k, n, alpha)
        
        # Lower bound should be high, close to 1
        assert 0.95 < lower < 1.0
        assert upper == 1.0

    def test_clopper_pearson_invalid_inputs(self):
        """Test handling of invalid inputs."""
        with pytest.raises(ValueError):
            calculate_confidence_interval(-1, 100)
        
        with pytest.raises(ValueError):
            calculate_confidence_interval(101, 100)
        
        with pytest.raises(ValueError):
            calculate_confidence_interval(10, 0)

class TestDeviationSummary:
    """Test T029: Deviation summary calculation."""

    def test_deviation_summary_structure(self):
        """Verify deviation summary returns correct columns."""
        data = {
            'p_value': [0.01, 0.06, 0.04],
            'scaling_method': ['standard', 'standard', 'minmax']
        }
        df = pd.DataFrame(data)
        summary = calculate_deviation_summary(df, alpha=0.05)
        
        assert 'scaling_method' in summary.columns
        assert 'empirical_rate' in summary.columns
        assert 'deviation' in summary.columns
        assert 'n_tests' in summary.columns