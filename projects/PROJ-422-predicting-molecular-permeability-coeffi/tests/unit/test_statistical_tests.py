import pytest
import numpy as np
import json
from pathlib import Path
import tempfile
import os

from analysis.statistical_tests import (
    calculate_cohens_d,
    calculate_confidence_interval,
    run_paired_ttest,
    update_metrics_file
)

class TestCohensD:
    def test_cohens_d_basic(self):
        """Test basic Cohen's d calculation"""
        group1 = np.array([10, 12, 14, 16, 18])
        group2 = np.array([8, 10, 12, 14, 16])
        
        d = calculate_cohens_d(group1, group2)
        
        # Expected: mean_diff = 2, pooled_std approx 2.828
        # d = 2 / 2.828 = 0.707
        assert 0.6 < d < 0.8, f"Expected d around 0.707, got {d}"
    
    def test_cohens_d_zero_std(self):
        """Test Cohen's d when standard deviation is zero"""
        group1 = np.array([10, 10, 10])
        group2 = np.array([10, 10, 10])
        
        d = calculate_cohens_d(group1, group2)
        assert d == 0.0, "Cohen's d should be 0 when there is no difference"

class TestConfidenceInterval:
    def test_ci_calculation(self):
        """Test confidence interval calculation"""
        diff_mean = 2.0
        diff_std = 1.0
        n = 30
        
        ci_lower, ci_upper = calculate_confidence_interval(diff_mean, diff_std, n)
        
        # Check that the interval is centered around the mean
        assert abs((ci_lower + ci_upper) / 2 - diff_mean) < 0.01
        assert ci_lower < diff_mean < ci_upper

class TestPairedTtest:
    def test_ttest_identical_groups(self):
        """Test t-test with identical groups (p-value should be 1.0)"""
        errors_a = np.array([1, 2, 3, 4, 5])
        errors_b = np.array([1, 2, 3, 4, 5])
        
        result = run_paired_ttest(errors_a, errors_b)
        
        assert result["p_value"] == 1.0, "p-value should be 1.0 for identical groups"
        assert result["mean_difference"] == 0.0
    
    def test_ttest_different_groups(self):
        """Test t-test with different groups"""
        errors_a = np.array([1, 2, 3, 4, 5])
        errors_b = np.array([5, 6, 7, 8, 9])
        
        result = run_paired_ttest(errors_a, errors_b)
        
        assert result["p_value"] < 0.05, "p-value should be significant for different groups"
        assert result["mean_difference"] == -4.0

class TestUpdateMetricsFile:
    def test_update_existing_file(self):
        """Test updating an existing metrics file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = Path(tmpdir) / "metrics.json"
            
            # Create initial metrics
            initial_metrics = {
                "model_metrics": {
                    "gnn": {"rmse": 0.5}
                }
            }
            
            with open(metrics_path, 'w') as f:
                json.dump(initial_metrics, f)
            
            # Update with t-test results
            ttest_results = {
                "t_statistic": 2.5,
                "p_value": 0.01,
                "mean_difference": 0.1,
                "std_difference": 0.05,
                "n_samples": 100,
                "degrees_of_freedom": 99
            }
            cohens_d = 0.5
            ci = (-0.05, 0.25)
            target_type = "experimental"
            
            update_metrics_file(metrics_path, ttest_results, cohens_d, ci, target_type)
            
            # Verify update
            with open(metrics_path, 'r') as f:
                updated_metrics = json.load(f)
            
            assert "statistical_tests" in updated_metrics
            assert updated_metrics["statistical_tests"]["cohens_d"] == cohens_d
            assert updated_metrics["statistical_tests"]["target_variable_type"] == target_type
            assert "gnn" in updated_metrics["model_metrics"] # Ensure original data preserved

if __name__ == "__main__":
    pytest.main([__file__, "-v"])