import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from modeling import calculate_empirical_pvalue, load_null_distribution, save_null_distribution, calculate_observed_metric
from sklearn.linear_model import ElasticNet

class TestCalculateEmpiricalPvalue:
    """Unit tests for empirical p-value calculation."""
    
    def test_pvalue_calculation_basic(self):
        """Test basic p-value calculation with known values."""
        observed_r = 0.5
        # Create a null distribution where 10% of values are >= 0.5
        null_dist = np.concatenate([
            np.random.normal(0, 0.1, 900),  # 900 values around 0
            np.random.uniform(0.5, 0.8, 100)  # 100 values >= 0.5
        ])
        
        p_value = calculate_empirical_pvalue(observed_r, null_dist)
        
        # Should be approximately 0.1 (100/1000)
        assert 0.09 <= p_value <= 0.11, f"Expected p-value around 0.1, got {p_value}"
        
    def test_pvalue_calculation_two_tailed(self):
        """Test that p-value calculation is two-tailed."""
        observed_r = -0.5
        # Create a null distribution symmetric around 0
        null_dist = np.random.normal(0, 0.1, 1000)
        # Add some extreme values
        null_dist = np.concatenate([null_dist, [-0.6, -0.7, 0.6, 0.7]])
        
        p_value = calculate_empirical_pvalue(observed_r, null_dist)
        
        # Should be small but non-zero
        assert 0 < p_value <= 1.0
        
    def test_pvalue_calculation_extreme_observed(self):
        """Test p-value when observed value is extreme."""
        observed_r = 0.9
        null_dist = np.random.normal(0, 0.1, 1000)
        
        p_value = calculate_empirical_pvalue(observed_r, null_dist)
        
        # Should be very small or zero
        assert p_value <= 0.01
        
    def test_pvalue_calculation_no_extreme(self):
        """Test p-value when observed value is not extreme."""
        observed_r = 0.1
        null_dist = np.random.normal(0, 0.1, 1000)
        
        p_value = calculate_empirical_pvalue(observed_r, null_dist)
        
        # Should be relatively large
        assert p_value > 0.1
        
    def test_empty_null_distribution(self):
        """Test that empty null distribution raises error."""
        observed_r = 0.5
        null_dist = np.array([])
        
        with pytest.raises(ValueError, match="Null distribution is empty"):
            calculate_empirical_pvalue(observed_r, null_dist)
            
    def test_single_value_null_distribution(self):
        """Test p-value calculation with single value in null distribution."""
        observed_r = 0.5
        null_dist = np.array([0.3])  # Less than observed
        
        p_value = calculate_empirical_pvalue(observed_r, null_dist)
        assert p_value == 0.0  # No values >= 0.5
        
        null_dist = np.array([0.6])  # Greater than observed
        p_value = calculate_empirical_pvalue(observed_r, null_dist)
        assert p_value == 1.0  # All values >= 0.5
        
class TestLoadSaveNullDistribution:
    """Tests for loading and saving null distributions."""
    
    def test_save_and_load_npy(self):
        """Test saving and loading null distribution in npy format."""
        null_dist = np.random.normal(0, 0.1, 1000)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "null_dist.npy"
            save_null_distribution(null_dist, path)
            
            loaded_dist = load_null_distribution(path)
            np.testing.assert_array_almost_equal(null_dist, loaded_dist)
            
    def test_save_and_load_csv(self):
        """Test saving and loading null distribution in csv format."""
        null_dist = np.random.normal(0, 0.1, 1000)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "null_dist.csv"
            save_null_distribution(null_dist, path)
            
            loaded_dist = load_null_distribution(path)
            np.testing.assert_array_almost_equal(null_dist, loaded_dist)
            
    def test_unsupported_format(self):
        """Test that unsupported file format raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "null_dist.txt"
            with open(path, 'w') as f:
                f.write("dummy")
                
            with pytest.raises(ValueError, match="Unsupported file format"):
                load_null_distribution(path)
                
class TestCalculateObservedMetric:
    """Tests for calculating observed correlation metric."""
    
    def test_calculate_observed_metric(self):
        """Test calculation of observed Pearson r."""
        # Create synthetic data with known correlation
        np.random.seed(42)
        X = np.random.randn(100, 5)
        y = X[:, 0] * 2 + np.random.randn(100) * 0.5
        
        model = ElasticNet(alpha=0.5, random_state=42)
        model.fit(X, y)
        
        r = calculate_observed_metric(X, y, model)
        
        # Should be a valid correlation coefficient
        assert -1.0 <= r <= 1.0
        # Should be positive since y is positively correlated with X[:, 0]
        assert r > 0.5