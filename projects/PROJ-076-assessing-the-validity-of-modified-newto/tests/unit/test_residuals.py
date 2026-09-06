import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from residuals import (
    calculate_residuals,
    block_bootstrap_permutation_test,
    holm_bonferroni_correction,
    generate_residual_stats
)
from utils import set_global_seed

class TestCalculateResiduals:
    def test_basic_residuals(self):
        """Test basic residual calculation"""
        observed = np.array([1.0, 2.0, 3.0, 4.0])
        predicted = np.array([1.1, 2.1, 2.9, 4.2])
        
        residuals = calculate_residuals(observed, predicted)
        
        expected = np.array([-0.1, -0.1, 0.1, -0.2])
        np.testing.assert_array_almost_equal(residuals, expected)
    
    def test_weighted_residuals(self):
        """Test residuals with uncertainty weighting"""
        observed = np.array([1.0, 2.0, 3.0])
        predicted = np.array([1.5, 2.5, 3.5])
        uncertainty = np.array([0.5, 0.5, 0.5])
        
        residuals = calculate_residuals(observed, predicted, uncertainty)
        
        expected = np.array([-1.0, -1.0, -1.0])
        np.testing.assert_array_almost_equal(residuals, expected)
    
    def test_empty_arrays(self):
        """Test with empty arrays"""
        observed = np.array([])
        predicted = np.array([])
        
        residuals = calculate_residuals(observed, predicted)
        assert len(residuals) == 0

class TestBlockBootstrapPermutationTest:
    def setup_method(self):
        """Set up test fixtures"""
        set_global_seed(42)
        self.residuals_by_galaxy = {
            'galaxy1': np.array([0.1, -0.2, 0.3, -0.1, 0.2]),
            'galaxy2': np.array([-0.1, 0.2, -0.3, 0.1, -0.2]),
            'galaxy3': np.array([0.05, -0.05, 0.0, 0.1, -0.1])
        }
    
    def test_basic_bootstrap(self):
        """Test basic bootstrap permutation test"""
        result = block_bootstrap_permutation_test(
            residuals_by_galaxy=self.residuals_by_galaxy,
            n_bootstrap=100,
            random_seed=42
        )
        
        assert 'p_value' in result
        assert 'observed_mean' in result
        assert 'bootstrap_distribution' in result
        assert 'confidence_interval' in result
        assert 'reject_null' in result
        
        assert 0.0 <= result['p_value'] <= 1.0
        assert len(result['bootstrap_distribution']) == 100
    
    def test_known_mean_zero(self):
        """Test with residuals that have mean close to zero"""
        set_global_seed(123)
        symmetric_residuals = {
            'galaxy1': np.array([-1.0, 1.0, -1.0, 1.0]),
            'galaxy2': np.array([0.5, -0.5, 0.5, -0.5])
        }
        
        result = block_bootstrap_permutation_test(
            residuals_by_galaxy=symmetric_residuals,
            n_bootstrap=500,
            random_seed=123
        )
        
        # With symmetric residuals, p-value should be relatively high
        # (not rejecting the null that mean = 0)
        assert result['observed_mean'] < 0.5  # Should be close to 0
    
    def test_empty_galaxies(self):
        """Test with no galaxies"""
        result = block_bootstrap_permutation_test(
            residuals_by_galaxy={},
            n_bootstrap=100
        )
        
        assert result['p_value'] == 1.0
        assert result['reject_null'] == False
        assert len(result['bootstrap_distribution']) == 0

class TestHolmBonferroniCorrection:
    def test_basic_correction(self):
        """Test basic Holm-Bonferroni correction"""
        p_values = [0.01, 0.03, 0.05, 0.10]
        
        result = holm_bonferroni_correction(p_values, alpha=0.05)
        
        assert 'corrected_p_values' in result
        assert 'rejected' in result
        assert 'thresholds' in result
        
        assert len(result['corrected_p_values']) == 4
        assert len(result['rejected']) == 4
        assert len(result['thresholds']) == 4
    
    def test_monotonicity(self):
        """Test that corrected p-values are monotonic"""
        p_values = [0.01, 0.02, 0.03, 0.04]
        
        result = holm_bonferroni_correction(p_values, alpha=0.05)
        
        corrected = result['corrected_p_values']
        for i in range(len(corrected) - 1):
            assert corrected[i] <= corrected[i+1]
    
    def test_empty_list(self):
        """Test with empty p-value list"""
        result = holm_bonferroni_correction([], alpha=0.05)
        
        assert result['corrected_p_values'] == []
        assert result['rejected'] == []
        assert result['thresholds'] == []
    
    def test_all_rejected(self):
        """Test case where all hypotheses are rejected"""
        p_values = [0.001, 0.002, 0.003]
        
        result = holm_bonferroni_correction(p_values, alpha=0.05)
        
        # With such small p-values, all should be rejected
        assert all(result['rejected'])
    
    def test_none_rejected(self):
        """Test case where no hypotheses are rejected"""
        p_values = [0.1, 0.2, 0.3, 0.4]
        
        result = holm_bonferroni_correction(p_values, alpha=0.05)
        
        # With large p-values, none should be rejected
        assert not any(result['rejected'])

class TestGenerateResidualStats:
    def test_basic_stats_generation(self):
        """Test basic residual statistics generation"""
        set_global_seed(42)
        
        # Create mock fit results
        fit_results = pd.DataFrame({
            'galaxy': ['galaxy1', 'galaxy1', 'galaxy2', 'galaxy2'],
            'model': ['MOND', 'NFW', 'MOND', 'NFW'],
            'reduced_chi2': [1.2, 1.5, 1.1, 1.3],
            'n_points': [20, 20, 25, 25]
        })
        
        # Create mock residuals
        residuals_dict = {
            'MOND': {
                'galaxy1': np.random.normal(0, 0.1, 20),
                'galaxy2': np.random.normal(0, 0.1, 25)
            },
            'NFW': {
                'galaxy1': np.random.normal(0, 0.1, 20),
                'galaxy2': np.random.normal(0, 0.1, 25)
            }
        }
        
        output_path = "/tmp/test_residual_stats.csv"
        
        stats_df = generate_residual_stats(
            fit_results=fit_results,
            residuals_dict=residuals_dict,
            output_path=output_path
        )
        
        # Check output
        assert len(stats_df) == 4
        assert 'mean_residual' in stats_df.columns
        assert 'std_residual' in stats_df.columns
        assert 'rmse' in stats_df.columns
        
        # Check file was created
        assert Path(output_path).exists()
        
        # Cleanup
        os.remove(output_path)
    
    def test_missing_fit_results(self):
        """Test behavior when fit results are missing for a galaxy"""
        fit_results = pd.DataFrame({
            'galaxy': ['galaxy1'],
            'model': ['MOND'],
            'reduced_chi2': [1.2]
        })
        
        residuals_dict = {
            'MOND': {
                'galaxy1': np.array([0.1, -0.1]),
                'galaxy2': np.array([0.2, -0.2])  # Not in fit_results
            }
        }
        
        output_path = "/tmp/test_missing_stats.csv"
        
        # Should complete without error, just skip missing galaxies
        stats_df = generate_residual_stats(
            fit_results=fit_results,
            residuals_dict=residuals_dict,
            output_path=output_path
        )
        
        assert len(stats_df) == 1  # Only galaxy1
        
        # Cleanup
        os.remove(output_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])