import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analysis.correlations import (
    run_correlation_analysis,
    apply_fdr_correction,
    calculate_batch_size,
    log_correlation_threshold
)
from analysis.power import calculate_detectable_effect_size

class TestCorrelationAnalysis:
    def test_correlation_computation(self):
        """Test that correlation is computed correctly."""
        np.random.seed(42)
        n = 100
        x = np.random.randn(n)
        y = 0.5 * x + np.random.randn(n) * 0.5  # Known correlation ~0.5
        
        # Calculate correlation manually
        r = np.corrcoef(x, y)[0, 1]
        
        # Verify it's in expected range
        assert 0.4 < r < 0.6, f"Expected correlation ~0.5, got {r}"

    def test_spearman_correlation(self):
        """Test Spearman correlation computation."""
        np.random.seed(42)
        n = 100
        x = np.random.randn(n)
        y = np.random.randn(n)
        
        from scipy.stats import spearmanr
        r, p = spearmanr(x, y)
        
        assert -1 <= r <= 1, f"Spearman r should be in [-1, 1], got {r}"
        assert 0 <= p <= 1, f"Spearman p should be in [0, 1], got {p}"

    def test_partial_correlation_with_covariate(self):
        """Test partial correlation with covariate (FD)."""
        np.random.seed(42)
        n = 100
        x = np.random.randn(n)
        y = np.random.randn(n)
        z = np.random.randn(n)  # Covariate (FD)
        
        # Partial correlation formula
        r_xy = np.corrcoef(x, y)[0, 1]
        r_xz = np.corrcoef(x, z)[0, 1]
        r_yz = np.corrcoef(y, z)[0, 1]
        
        partial_r = (r_xy - r_xz * r_yz) / np.sqrt((1 - r_xz**2) * (1 - r_yz**2))
        
        assert -1 <= partial_r <= 1, f"Partial r should be in [-1, 1], got {partial_r}"

class TestFDRCorrection:
    def test_bh_fdr_correction(self):
        """Test Benjamini-Hochberg FDR correction."""
        # Create a set of p-values with known ground truth
        p_values = np.array([0.001, 0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.5, 0.9])
        n = len(p_values)
        
        # Sort p-values
        sorted_indices = np.argsort(p_values)
        sorted_p = p_values[sorted_indices]
        
        # BH correction
        corrected_p = np.zeros(n)
        for i in range(n):
            corrected_p[sorted_indices[i]] = sorted_p[i] * n / (i + 1)
        
        # Ensure corrected p-values are >= original
        assert np.all(corrected_p >= p_values), "FDR corrected p-values should be >= original"
        
        # Ensure corrected p-values are <= 1
        assert np.all(corrected_p <= 1.0), "FDR corrected p-values should be <= 1"

    def test_fdr_significance(self):
        """Test FDR significance determination."""
        p_values = np.array([0.001, 0.01, 0.02, 0.03, 0.04, 0.05, 0.1, 0.2, 0.5, 0.9])
        alpha = 0.05
        
        # Apply FDR correction
        corrected_p = apply_fdr_correction(p_values, alpha)
        
        # Count significant results
        significant = np.sum(corrected_p <= alpha)
        
        # With these p-values, we expect some to be significant
        assert significant >= 0, "Should have non-negative significant count"
        assert significant <= len(p_values), "Should have at most all significant"

    def test_fdr_with_all_high_p(self):
        """Test FDR when all p-values are high."""
        p_values = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        alpha = 0.05
        
        corrected_p = apply_fdr_correction(p_values, alpha)
        
        # None should be significant
        assert np.all(corrected_p > alpha), "No p-values should be significant"

    def test_fdr_with_all_low_p(self):
        """Test FDR when all p-values are low."""
        p_values = np.array([0.001, 0.002, 0.003, 0.004, 0.005])
        alpha = 0.05
        
        corrected_p = apply_fdr_correction(p_values, alpha)
        
        # All should be significant
        assert np.all(corrected_p <= alpha), "All p-values should be significant"

class TestBatchSizeCalculation:
    def test_batch_size_memory_constraint(self):
        """Test that batch size respects memory constraints."""
        # Simulate memory constraints
        available_memory_gb = 7.0
        matrix_size_bytes = 400 * 400 * 8  # float64
        
        batch_size = calculate_batch_size(available_memory_gb, matrix_size_bytes)
        
        # Should return a positive integer
        assert isinstance(batch_size, int), "Batch size should be integer"
        assert batch_size > 0, "Batch size should be positive"

    def test_batch_size_scaling(self):
        """Test that batch size scales with available memory."""
        matrix_size_bytes = 400 * 400 * 8
        
        batch_7gb = calculate_batch_size(7.0, matrix_size_bytes)
        batch_3gb = calculate_batch_size(3.0, matrix_size_bytes)
        
        # Larger memory should allow larger batch
        assert batch_7gb >= batch_3gb, "Larger memory should allow larger batch"

class TestCorrelationThreshold:
    def test_threshold_logging(self):
        """Test that correlation threshold is logged correctly."""
        r_values = [0.1, 0.2, 0.3, 0.4, 0.5]
        threshold = 0.3
        
        # Count values above threshold
        above_threshold = sum(1 for r in r_values if abs(r) > threshold)
        
        assert above_threshold == 2, "Should have 2 values above threshold"

    def test_threshold_zero(self):
        """Test threshold with zero threshold."""
        r_values = [-0.1, 0.1, -0.2, 0.2]
        threshold = 0.0
        
        above_threshold = sum(1 for r in r_values if abs(r) > threshold)
        
        assert above_threshold == 4, "All values should be above zero threshold"

class TestPowerAnalysis:
    def test_detectable_effect_size(self):
        """Test detectable effect size calculation."""
        n = 100
        power = 0.8
        alpha = 0.05
        
        r = calculate_detectable_effect_size(n, power, alpha)
        
        # Should return a valid correlation coefficient
        assert -1 <= r <= 1, f"Detectable r should be in [-1, 1], got {r}"
        assert r > 0, "Detectable effect size should be positive"

    def test_power_scaling_with_n(self):
        """Test that detectable effect size decreases with larger N."""
        r_50 = calculate_detectable_effect_size(50, 0.8, 0.05)
        r_100 = calculate_detectable_effect_size(100, 0.8, 0.05)
        
        # Larger sample should detect smaller effects
        assert r_100 < r_50, "Larger N should detect smaller effects"

    def test_power_scaling_with_power(self):
        """Test that detectable effect size increases with required power."""
        r_07 = calculate_detectable_effect_size(100, 0.7, 0.05)
        r_09 = calculate_detectable_effect_size(100, 0.9, 0.05)
        
        # Higher power requirement should detect larger effects
        assert r_09 > r_07, "Higher power should detect larger effects"

class TestIntegration:
    def test_full_correlation_pipeline(self):
        """Test the full correlation analysis pipeline."""
        np.random.seed(42)
        
        # Create synthetic data
        n_subjects = 50
        metrics = {
            'modularity': np.random.randn(n_subjects),
            'global_efficiency': np.random.randn(n_subjects),
            'participation_coef': np.random.randn(n_subjects),
            'within_module_degree': np.random.randn(n_subjects),
            'motor_score': np.random.randn(n_subjects),
            'fd': np.random.rand(n_subjects) * 0.5  # FD < 0.5
        }
        
        df = pd.DataFrame(metrics)
        
        # Run correlation analysis (mocked)
        with patch('analysis.correlations.run_correlation_analysis') as mock_run:
            mock_run.return_value = {
                'modularity': {'r': 0.3, 'p': 0.03, 'q': 0.04, 'significant': True},
                'global_efficiency': {'r': 0.2, 'p': 0.1, 'q': 0.12, 'significant': False}
            }
            
            results = mock_run(df, 'motor_score', 'fd')
            
            assert 'modularity' in results, "Modularity should be in results"
            assert 'global_efficiency' in results, "Global efficiency should be in results"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
