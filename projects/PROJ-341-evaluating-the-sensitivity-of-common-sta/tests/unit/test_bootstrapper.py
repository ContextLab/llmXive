"""
Unit tests for the bootstrapper module (T032).
"""
import pytest
import numpy as np
import pandas as pd
import os
import json
import tempfile
from scipy import stats

from code.analysis.bootstrapper import (
    bootstrap_power_estimate,
    calculate_ks_distance,
    load_real_data_pvalues,
    load_simulated_power_distribution,
    run_bootstrapped_validation,
    save_power_results
)

class TestBootstrapPowerEstimate:
    """Tests for bootstrap_power_estimate function."""
    
    def test_bootstrap_power_estimate_basic(self):
        """Test basic bootstrap power estimation."""
        # Create p-values with known significance rate
        p_values = [0.01, 0.02, 0.03, 0.6, 0.7, 0.8]  # 3/6 < 0.05
        result = bootstrap_power_estimate(p_values, alpha=0.05, n_bootstrap=100, rng=np.random.default_rng(42))
        
        assert "power_estimate" in result
        assert "ci_lower" in result
        assert "ci_upper" in result
        assert "se" in result
        assert result["n_bootstrap"] == 100
        assert result["n_observations"] == 6
        
        # Power should be around 0.5 given 3/6 are significant
        assert 0.3 < result["power_estimate"] < 0.7
        
    def test_bootstrap_power_estimate_empty(self):
        """Test bootstrap with empty p-values."""
        result = bootstrap_power_estimate([], alpha=0.05, n_bootstrap=100)
        
        assert result["power_estimate"] == 0.0
        assert result["ci_lower"] == 0.0
        assert result["ci_upper"] == 0.0
        assert result["se"] == 0.0
        
    def test_bootstrap_power_estimate_all_significant(self):
        """Test bootstrap when all p-values are significant."""
        p_values = [0.01, 0.02, 0.03, 0.04, 0.045]
        result = bootstrap_power_estimate(p_values, alpha=0.05, n_bootstrap=100, rng=np.random.default_rng(42))
        
        # Should be close to 1.0
        assert result["power_estimate"] > 0.9

class TestCalculateKsDistance:
    """Tests for calculate_ks_distance function."""
    
    def test_ks_distance_identical_distributions(self):
        """Test KS distance with identical distributions."""
        real = [0.1, 0.2, 0.3, 0.4, 0.5]
        sim = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        dist = calculate_ks_distance(real, sim)
        
        # Should be close to 0 for identical distributions
        assert dist < 0.2
        
    def test_ks_distance_different_distributions(self):
        """Test KS distance with different distributions."""
        real = [0.01, 0.02, 0.03, 0.04, 0.05]  # Small values
        sim = [0.5, 0.6, 0.7, 0.8, 0.9]  # Large values
        
        dist = calculate_ks_distance(real, sim)
        
        # Should be larger for different distributions
        assert dist > 0.3
        
    def test_ks_distance_empty(self):
        """Test KS distance with empty lists."""
        dist = calculate_ks_distance([], [0.1, 0.2, 0.3])
        
        assert dist == 1.0  # Maximum distance

class TestRunBootstrappedValidation:
    """Tests for run_bootstrapped_validation function."""
    
    def test_validation_structure(self):
        """Test that validation returns correct structure."""
        # Create mock data
        real_pvalues = pd.DataFrame({
            'test_type': ['t-test', 't-test', 'anova', 'anova'],
            'p_value': [0.01, 0.03, 0.02, 0.04],
            'sample_size': [10, 10, 20, 20],
            'effect_size': [0.5, 0.5, 0.5, 0.5]
        })
        
        simulated_error_rates = pd.DataFrame({
            'test_type': ['t-test', 't-test', 'anova', 'anova'],
            'effect_size': [0.0, 0.5, 0.0, 0.5],
            'type_i_error_rate': [0.05, 0.05, 0.05, 0.05],
            'power': [0.05, 0.8, 0.05, 0.8]
        })
        
        results = run_bootstrapped_validation(real_pvalues, simulated_error_rates, n_bootstrap=50)
        
        assert 't-test' in results
        assert 'anova' in results
        
        for test_type, result in results.items():
            assert 'power_estimate' in result
            assert 'ks_distance' in result
            assert 'passes_validation' in result
            assert 'threshold' in result
            
    def test_validation_passes_threshold(self):
        """Test validation that passes the KS threshold."""
        # Create p-values close to uniform (null hypothesis)
        rng = np.random.default_rng(42)
        real_pvalues = pd.DataFrame({
            'test_type': ['t-test'] * 100,
            'p_value': rng.uniform(0, 1, 100),
            'sample_size': [10] * 100,
            'effect_size': [0.0] * 100
        })
        
        simulated_error_rates = pd.DataFrame({
            'test_type': ['t-test'],
            'effect_size': [0.0],
            'type_i_error_rate': [0.05],
            'power': [0.05]
        })
        
        results = run_bootstrapped_validation(real_pvalues, simulated_error_rates, n_bootstrap=50)
        
        # Should pass validation (KS <= 0.10) for uniform-like distribution
        assert results['t-test']['passes_validation'] == True
        assert results['t-test']['ks_distance'] <= 0.10

class TestSavePowerResults:
    """Tests for save_power_results function."""
    
    def test_save_and_load(self):
        """Test that results can be saved and loaded."""
        results = {
            't-test': {
                'power_estimate': {'power_estimate': 0.5, 'ci_lower': 0.4, 'ci_upper': 0.6},
                'ks_distance': 0.05,
                'passes_validation': True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            
        try:
            save_power_results(results, temp_path)
            
            assert os.path.exists(temp_path)
            
            with open(temp_path, 'r') as f:
                loaded = json.load(f)
                
            assert 't-test' in loaded
            assert loaded['t-test']['ks_distance'] == 0.05
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])