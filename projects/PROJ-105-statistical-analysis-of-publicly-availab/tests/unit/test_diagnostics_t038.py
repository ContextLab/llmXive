import pytest
import numpy as np
from scipy import stats
import json
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, 'code')

from diagnostics import tail_ks_test, log_normal_discrimination

class TestTailKS:
    def test_tail_ks_test_structure(self, tmp_path):
        """Test that tail_ks_test returns expected dictionary structure."""
        # Create synthetic data that follows a known distribution
        # Generate exponential data (light tail)
        np.random.seed(42)
        data = np.random.exponential(scale=10.0, size=1000)
        
        # Fit a model (exponential)
        fitted_model = stats.expon.fit(data)
        fitted_model = stats.expon(*fitted_model)
        
        x_min = 1.0
        
        # Run test with small bootstrap for speed
        result = tail_ks_test(
            data=data,
            fitted_model=fitted_model,
            x_min=x_min,
            n_bootstrap=10,
            seed=42
        )
        
        assert isinstance(result, dict)
        assert "ks_statistic" in result
        assert "p_value" in result
        assert "n_bootstrap" in result
        assert "x_min" in result
        assert isinstance(result["ks_statistic"], float)
        assert isinstance(result["p_value"], float)
        assert 0.0 <= result["p_value"] <= 1.0

    def test_tail_ks_test_insufficient_data(self):
        """Test behavior with insufficient tail data."""
        data = np.array([1.0, 2.0, 3.0])
        fitted_model = stats.expon(0, 1)
        
        result = tail_ks_test(
            data=data,
            fitted_model=fitted_model,
            x_min=2.0,
            n_bootstrap=10,
            seed=42
        )
        
        assert "error" in result
        assert "p_value" not in result or result["p_value"] is None

    def test_tail_ks_test_pareto_fit(self):
        """Test fitting Pareto on tail data."""
        # Generate Pareto data
        np.random.seed(42)
        # alpha=2.5, scale=1.0
        data = stats.pareto.rvs(2.5, scale=1.0, size=500)
        
        x_min = 1.0
        tail_data = data[data >= x_min]
        
        # Fit Pareto
        b, loc, scale = stats.pareto.fit(tail_data, floc=x_min)
        fitted_model = stats.pareto(b, loc=loc, scale=scale)
        
        result = tail_ks_test(
            data=tail_data,
            fitted_model=fitted_model,
            x_min=x_min,
            n_bootstrap=10,
            seed=42
        )
        
        assert result["p_value"] is not None
        assert result["ks_statistic"] > 0

class TestLogNormalDiscrimination:
    def test_log_normal_discrimination_structure(self):
        """Test structure of log_normal_discrimination output."""
        np.random.seed(42)
        # Generate log-normal data
        data = stats.lognorm.rvs(s=1.0, scale=np.exp(0), size=500)
        
        x_min = 1.0
        result = log_normal_discrimination(data, x_min, n_sim=10)
        
        assert isinstance(result, dict)
        assert "observed_curvature" in result
        assert "mean_simulated_curvature" in result
        assert "p_value" in result
        assert "interpretation" in result

    def test_log_normal_discrimination_insufficient_data(self):
        """Test with insufficient data."""
        data = np.array([1.0, 2.0])
        x_min = 1.0
        result = log_normal_discrimination(data, x_min, n_sim=10)
        
        assert "error" in result