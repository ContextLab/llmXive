import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

# Import the module under test
from code.analysis.bootstrapper import (
    bootstrap_power_estimate,
    calculate_ks_distance,
    load_real_data_pvalues,
    save_power_results
)

class TestBootstrapPowerEstimate:
    """Tests for bootstrap_power_estimate function."""

    def test_power_estimate_basic(self):
        """Test basic power estimation with known p-values."""
        # Create p-values where 50% are < 0.05
        p_values = pd.Series([0.01, 0.02, 0.4, 0.5, 0.6, 0.7])
        result = bootstrap_power_estimate(p_values, n_bootstraps=100, alpha=0.05)
        
        assert 'power_estimate' in result
        assert 'ci_lower' in result
        assert 'ci_upper' in result
        assert result['n_samples'] == 6
        assert result['n_bootstraps'] == 100
        
        # Observed power should be 2/6 = 0.333
        assert abs(result['power_estimate'] - 0.333) < 0.01

    def test_power_estimate_all_significant(self):
        """Test power estimation when all p-values are significant."""
        p_values = pd.Series([0.01, 0.02, 0.03, 0.04])
        result = bootstrap_power_estimate(p_values, n_bootstraps=50, alpha=0.05)
        
        assert result['power_estimate'] == 1.0
        assert result['ci_lower'] == 1.0
        assert result['ci_upper'] == 1.0

    def test_power_estimate_none_significant(self):
        """Test power estimation when no p-values are significant."""
        p_values = pd.Series([0.1, 0.2, 0.3, 0.4, 0.5])
        result = bootstrap_power_estimate(p_values, n_bootstraps=50, alpha=0.05)
        
        assert result['power_estimate'] == 0.0

    def test_empty_pvalues_raises(self):
        """Test that empty p-values raise an error."""
        p_values = pd.Series([])
        with pytest.raises(ValueError, match="Cannot bootstrap with zero p-values"):
            bootstrap_power_estimate(p_values)

class TestCalculateKsDistance:
    """Tests for calculate_ks_distance function."""

    def test_ks_distance_identical_distributions(self):
        """Test KS distance with identical distributions (should be near 0)."""
        np.random.seed(42)
        dist1 = np.random.uniform(0, 1, 1000)
        dist2 = dist1.copy()
        
        ks = calculate_ks_distance(pd.Series(dist1), dist2)
        assert ks == 0.0

    def test_ks_distance_different_distributions(self):
        """Test KS distance with different distributions."""
        # Uniform vs concentrated near 0
        uniform = np.random.uniform(0, 1, 1000)
        concentrated = np.random.beta(0.5, 1, 1000)
        
        ks = calculate_ks_distance(pd.Series(uniform), concentrated)
        
        # Should be significantly greater than 0
        assert ks > 0.1
        assert ks <= 1.0

    def test_ks_distance_empty_raises(self):
        """Test that empty distributions raise an error."""
        with pytest.raises(ValueError, match="Cannot calculate KS distance"):
            calculate_ks_distance(pd.Series([]), np.array([]))

class TestSavePowerResults:
    """Tests for save_power_results function."""

    def test_save_results_creates_file(self):
        """Test that save_power_results creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_results.json")
            results = {
                "t-test": {
                    "power_estimate": 0.8,
                    "ks_distance": 0.05,
                    "ks_pass": True
                }
            }
            
            save_power_results(results, output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert 'timestamp' in data
            assert 'results_by_test_type' in data
            assert data['results_by_test_type']['t-test']['power_estimate'] == 0.8

    def test_save_results_structure(self):
        """Test the structure of saved results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_results.json")
            results = {
                "t-test": {
                    "power_estimate": 0.8,
                    "power_ci_lower": 0.7,
                    "power_ci_upper": 0.9,
                    "ks_distance": 0.05,
                    "ks_threshold": 0.10,
                    "ks_pass": True,
                    "n_real_samples": 100,
                    "datasets_included": ["dataset1"]
                }
            }
            
            save_power_results(results, output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data['alpha'] == 0.05
            assert data['ks_threshold'] == 0.10
            assert 'timestamp' in data
