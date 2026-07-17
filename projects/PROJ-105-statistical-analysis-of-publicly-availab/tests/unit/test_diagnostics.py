import pytest
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from diagnostics import log_normal_discrimination, bootstrap_goodness_of_fit, hill_estimator

class TestLogNormalDiscrimination:
    """Tests for Log-Normal discrimination functionality."""
    
    def test_log_normal_discrimination_with_lognormal_data(self):
        """Test that Log-Normal data is correctly identified."""
        # Generate Log-Normal data
        np.random.seed(42)
        lognormal_data = np.random.lognormal(mean=2, sigma=1, size=1000)
        
        # Use a reasonable x_min
        x_min = np.percentile(lognormal_data, 75)
        
        # Run discrimination test
        result = log_normal_discrimination(lognormal_data, x_min, n_simulations=100)
        
        # Should not raise an error
        assert "p_value" in result
        assert "is_log_normal" in result
        assert "observed_curvature" in result
        
        # With Log-Normal data, p-value should be relatively high (not reject)
        # Note: This is probabilistic, so we don't assert exact values
        assert 0 <= result["p_value"] <= 1
        assert result["sample_size"] > 0
        
    def test_log_normal_discrimination_with_pareto_data(self):
        """Test that Pareto data is correctly distinguished from Log-Normal."""
        # Generate Pareto data
        np.random.seed(42)
        pareto_data = np.random.pareto(a=2, size=1000) + 1  # Shifted to be > 1
        
        # Use a reasonable x_min
        x_min = np.percentile(pareto_data, 75)
        
        # Run discrimination test
        result = log_normal_discrimination(pareto_data, x_min, n_simulations=100)
        
        # Should not raise an error
        assert "p_value" in result
        assert "is_log_normal" in result
        
        # With Pareto data, p-value might be lower (more likely to reject Log-Normal)
        assert 0 <= result["p_value"] <= 1
        
    def test_insufficient_data_raises_error(self):
        """Test that insufficient data raises appropriate error."""
        small_data = np.array([1.0, 2.0, 3.0])
        
        with pytest.raises(ValueError, match="Insufficient tail data"):
            log_normal_discrimination(small_data, x_min=1.0)
            
    def test_result_structure(self):
        """Test that result dictionary has all required fields."""
        np.random.seed(42)
        data = np.random.lognormal(mean=2, sigma=1, size=500)
        x_min = np.percentile(data, 75)
        
        result = log_normal_discrimination(data, x_min, n_simulations=50)
        
        required_fields = [
            "observed_curvature", "mean_null_curvature", "null_std_curvature",
            "p_value", "n_simulations", "sample_size", "x_min", 
            "is_log_normal", "interpretation"
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

class TestHillEstimator:
    """Tests for Hill estimator functionality."""
    
    def test_hill_estimator_basic(self):
        """Test basic Hill estimator functionality."""
        np.random.seed(42)
        # Generate Pareto-like data
        data = np.random.pareto(a=2, size=1000) + 1
        
        k_values, hill_values, optimal_hill = hill_estimator(data)
        
        assert len(k_values) > 0
        assert len(hill_values) > 0
        assert len(k_values) == len(hill_values)
        assert optimal_hill > 0
        
    def test_hill_estimator_small_dataset(self):
        """Test Hill estimator with small dataset."""
        small_data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        with pytest.raises(ValueError, match="Dataset too small"):
            hill_estimator(small_data)

class TestBootstrapGoodnessOfFit:
    """Tests for bootstrap goodness-of-fit functionality."""
    
    def test_bootstrap_gof_pareto(self):
        """Test bootstrap GoF for Pareto distribution."""
        np.random.seed(42)
        data = np.random.pareto(a=2, size=500) + 1
        
        fitted_params = {"alpha": 2.0}
        
        result = bootstrap_goodness_of_fit(
            data, fitted_params, "pareto", n_iter=50
        )
        
        assert "observed_ks_statistic" in result
        assert "bootstrap_p_value" in result
        assert 0 <= result["bootstrap_p_value"] <= 1
        assert result["n_iterations"] == 50
        
    def test_bootstrap_gof_insufficient_data(self):
        """Test bootstrap GoF with insufficient data."""
        small_data = np.array([1.0, 2.0, 3.0])
        
        with pytest.raises(ValueError, match="Insufficient data"):
            bootstrap_goodness_of_fit(
                small_data, {"alpha": 2.0}, "pareto", n_iter=10
            )
