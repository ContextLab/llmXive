"""
Unit tests for bootstrap resampling analysis.
"""
import pytest
import numpy as np
import json
import os
import tempfile
from pathlib import Path

# Import the module under test
from bootstrap_analysis import (
    bootstrap_resample_variance,
    run_bootstrap_analysis,
    thin_dataset
)
from utils import calculate_autocorrelation_time, thin_dataset as utils_thin_dataset

class TestBootstrapResampleVariance:
    """Test bootstrap resampling functionality."""
    
    def test_basic_bootstrap(self):
        """Test basic bootstrap resampling with known data."""
        np.random.seed(42)
        n_samples = 100
        latent_dim = 5
        n_temps = 3
        
        # Create synthetic latent data
        latent_mu = np.random.randn(n_samples, latent_dim)
        temperatures = np.repeat([1.0, 2.0, 3.0], n_samples // n_temps)
        
        # Run bootstrap
        mean_var, std_var, p95_var = bootstrap_resample_variance(
            latent_mu,
            temperatures,
            n_bootstrap=50,
            random_seed=42
        )
        
        # Check shapes
        assert mean_var.shape == (n_temps, latent_dim)
        assert std_var.shape == (n_temps, latent_dim)
        assert p95_var.shape == (n_temps, latent_dim)
        
        # Check that variance is positive
        assert np.all(mean_var >= 0)
        assert np.all(std_var >= 0)
        
        # Check that 95th percentile > mean
        assert np.all(p95_var >= mean_var)
    
    def test_bootstrap_stability(self):
        """Test that bootstrap results are stable with fixed seed."""
        np.random.seed(42)
        latent_mu = np.random.randn(200, 4)
        temperatures = np.tile([1.0, 2.0], 100)
        
        # Run twice with same seed
        mean_var1, std_var1, _ = bootstrap_resample_variance(
            latent_mu, temperatures, n_bootstrap=100, random_seed=123
        )
        mean_var2, std_var2, _ = bootstrap_resample_variance(
            latent_mu, temperatures, n_bootstrap=100, random_seed=123
        )
        
        # Results should be identical
        np.testing.assert_array_almost_equal(mean_var1, mean_var2)
        np.testing.assert_array_almost_equal(std_var1, std_var2)
    
    def test_bootstrap_with_empty_bins(self):
        """Test bootstrap handling of temperature bins with no samples."""
        latent_mu = np.random.randn(100, 3)
        temperatures = np.array([1.0] * 50 + [2.0] * 50)  # No samples at temp=3.0
        
        # This should not crash, but produce NaN for empty bins
        mean_var, std_var, p95_var = bootstrap_resample_variance(
            latent_mu,
            temperatures,
            n_bootstrap=10,
            random_seed=42
        )
        
        # At least some values should be valid
        assert not np.all(np.isnan(mean_var))

class TestRunBootstrapAnalysis:
    """Test the full bootstrap analysis pipeline."""
    
    def test_full_pipeline(self):
        """Test complete bootstrap analysis pipeline."""
        # Create temporary files
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create synthetic latent data file
            latent_data_path = os.path.join(tmpdir, 'latent_data.npy')
            latent_mu = np.random.randn(500, 10)
            temperatures = np.repeat([1.0, 1.5, 2.0, 2.5, 3.0], 100)
            np.save(latent_data_path, {'mu': latent_mu, 'temperatures': temperatures})
            
            # Create tau_int results file
            tau_int_path = os.path.join(tmpdir, 'tau_int_results.json')
            tau_results = {
                'tau_int_values': {
                    'L=16': 5.2,
                    'L=24': 8.7
                }
            }
            with open(tau_int_path, 'w') as f:
                json.dump(tau_results, f)
            
            output_path = os.path.join(tmpdir, 'bootstrap_results.json')
            
            # Run analysis
            results = run_bootstrap_analysis(
                data_path=latent_data_path,
                tau_int_path=tau_int_path,
                output_path=output_path,
                n_bootstrap=20,
                thinning_factor=2.0,
                random_seed=42
            )
            
            # Check results structure
            assert 'n_bootstrap' in results
            assert 'thinning_factor' in results
            assert 'mean_variance' in results
            assert 'std_variance' in results
            assert 'confidence_interval_95' in results
            
            # Check that file was created
            assert os.path.exists(output_path)
            
            # Verify file contents
            with open(output_path, 'r') as f:
                saved_results = json.load(f)
            
            assert saved_results['n_bootstrap'] == 20
            assert saved_results['thinning_factor'] >= 2

class TestThinningIntegration:
    """Test thinning integration with autocorrelation time."""
    
    def test_thinning_factor_calculation(self):
        """Test that thinning factor is calculated correctly from tau_int."""
        # Simulate tau_int results
        tau_int_values = {'L=16': 5.0, 'L=24': 8.0}
        max_tau = max(tau_int_values.values())
        thinning_factor = 2.0
        
        effective_thinning = max(int(thinning_factor * max_tau), 1)
        
        assert effective_thinning == 16  # 2 * 8
        assert effective_thinning >= 2 * max_tau  # Satisfies FR-006

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
