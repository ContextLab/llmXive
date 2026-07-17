import pytest
import numpy as np
from scipy import stats
import json
import os
import sys
import tempfile
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from models import (
    ConvergenceError,
    fit_distribution,
    get_fitted_distribution,
    compare_component_distributions
)

class TestFitDistribution:
    """Tests for fit_distribution function."""
    
    def test_fit_exponential(self):
        """Test fitting exponential distribution."""
        data = np.random.exponential(scale=2.0, size=1000)
        dist_obj, params = fit_distribution(data, 'expon')
        assert dist_obj is not None
        assert 'expon' in params['name']
        assert len(params['params']) > 0
        assert not any(np.isnan(p) for p in params['params'])
    
    def test_fit_gamma(self):
        """Test fitting gamma distribution."""
        data = np.random.gamma(shape=2.0, scale=1.5, size=1000)
        dist_obj, params = fit_distribution(data, 'gamma')
        assert dist_obj is not None
        assert 'gamma' in params['name']
        assert not any(np.isnan(p) for p in params['params'])
    
    def test_fit_lognorm(self):
        """Test fitting log-normal distribution."""
        data = np.random.lognormal(mean=0.0, sigma=1.0, size=1000)
        dist_obj, params = fit_distribution(data, 'lognorm')
        assert dist_obj is not None
        assert 'lognorm' in params['name']
        assert not any(np.isnan(p) for p in params['params'])
    
    def test_fit_weibull(self):
        """Test fitting Weibull distribution."""
        data = np.random.weibull(a=1.5, size=1000)
        dist_obj, params = fit_distribution(data, 'weibull_min')
        assert dist_obj is not None
        assert 'weibull_min' in params['name']
        assert not any(np.isnan(p) for p in params['params'])
    
    def test_fit_empty_data(self):
        """Test fitting with empty data raises error."""
        with pytest.raises(ConvergenceError):
            fit_distribution(np.array([]), 'expon')
    
    def test_fit_invalid_method(self):
        """Test fitting with invalid method raises error."""
        data = np.random.exponential(size=100)
        with pytest.raises(ValueError):
            fit_distribution(data, 'expon', method='invalid')

class TestGetFittedDistribution:
    """Tests for get_fitted_distribution function."""
    
    def test_get_metrics(self):
        """Test calculation of fit metrics."""
        data = np.random.exponential(scale=2.0, size=1000)
        dist_obj, _ = fit_distribution(data, 'expon')
        metrics = get_fitted_distribution(dist_obj, data)
        
        assert 'aic' in metrics
        assert 'bic' in metrics
        assert 'ks_statistic' in metrics
        assert 'ks_p_value' in metrics
        assert 'ad_statistic' in metrics
        
        # Check reasonable values
        assert metrics['ks_statistic'] >= 0
        assert 0 <= metrics['ks_p_value'] <= 1
        assert metrics['ad_statistic'] >= 0

class TestCompareComponentDistributions:
    """Tests for compare_component_distributions function."""
    
    def test_compare_distributions(self):
        """Test comparison of total vs component delays."""
        # Generate synthetic data for testing
        np.random.seed(42)
        n = 1000
        arr_delay = np.random.exponential(scale=5.0, size=n)
        dep_delay = np.random.exponential(scale=3.0, size=n)
        total_delay = arr_delay + dep_delay + np.random.normal(0, 1, size=n)
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            results = compare_component_distributions(total_delay, arr_delay, dep_delay, output_path)
            
            assert 'ks_tests' in results
            assert 'summary_statistics' in results
            
            # Check KS tests exist
            assert 'total_vs_arrival' in results['ks_tests']
            assert 'total_vs_departure' in results['ks_tests']
            assert 'arrival_vs_departure' in results['ks_tests']
            
            # Check summary statistics
            assert 'total_delay' in results['summary_statistics']
            assert 'arrival_delay' in results['summary_statistics']
            assert 'departure_delay' in results['summary_statistics']
            
            # Verify JSON file was created
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            assert loaded == results
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_compare_with_no_valid_data(self):
        """Test comparison with no valid data points."""
        total_delay = np.array([0.0, 0.0, 0.0])
        arr_delay = np.array([0.0, 0.0, 0.0])
        dep_delay = np.array([0.0, 0.0, 0.0])
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            results = compare_component_distributions(total_delay, arr_delay, dep_delay, output_path)
            assert results.get('error') == "No valid data points"
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
    
    def test_compare_with_partial_valid_data(self):
        """Test comparison with some valid data points."""
        np.random.seed(42)
        arr_delay = np.array([10.0, -5.0, 20.0, 0.0])  # -5 and 0 are invalid for some checks
        dep_delay = np.array([5.0, 10.0, -3.0, 0.0])
        total_delay = arr_delay + dep_delay + 1.0  # [16, 6, 18, 1]
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            results = compare_component_distributions(total_delay, arr_delay, dep_delay, output_path)
            assert 'ks_tests' in results
            assert 'summary_statistics' in results
            # Should have at least one valid point (index 0: 10+5+1=16)
            assert results['summary_statistics']['total_delay']['count'] >= 1
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)