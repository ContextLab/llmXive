import pytest
import numpy as np
import os
import json
import tempfile
from pathlib import Path
import csv

# Import the module
from code.generate_data import (
    streaming_data_generator,
    generate_correlated_data,
    generate_distribution_violations,
    HighDimensionalInstabilityError
)
from code.utils.simulation import RNGWrapper

class TestStreamingDataGenerator:
    
    def setup_method(self):
        """Create a temporary params.csv for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.params_file = Path(self.temp_dir) / "params.csv"
        
        # Create a small params.csv
        with open(self.params_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['n', 'p', 'rho', 'distribution_type', 'seed'])
            writer.writeheader()
            writer.writerow({'n': 50, 'p': 50, 'rho': 0.5, 'distribution_type': 'normal', 'seed': 42})
            writer.writerow({'n': 100, 'p': 200, 'rho': 0.1, 'distribution_type': 't', 'seed': 43})
            writer.writerow({'n': 50, 'p': 600, 'rho': 0.5, 'distribution_type': 'normal', 'seed': 44}) # p/n > 10 -> Should raise

    def test_generator_yields_data(self):
        """Test that the generator yields data and params."""
        results = []
        
        def callback(data, params):
            results.append((data, params))
            return True
        
        list(streaming_data_generator(str(self.params_file), callback))
        
        assert len(results) == 2 # First two rows should succeed
        data1, params1 = results[0]
        assert data1.shape == (50, 50)
        assert params1['seed'] == 42
        
        data2, params2 = results[1]
        assert data2.shape == (100, 200)
        assert params2['seed'] == 43

    def test_generator_raises_high_dimensional_instability(self):
        """Test that the generator raises error when p/n > 10."""
        def callback(data, params):
            return True
        
        with pytest.raises(HighDimensionalInstabilityError):
            list(streaming_data_generator(str(self.params_file), callback))

    def test_callback_stop(self):
        """Test that returning False from callback stops the generator."""
        count = 0
        def callback(data, params):
            nonlocal count
            count += 1
            return False # Stop after first
        
        list(streaming_data_generator(str(self.params_file), callback))
        assert count == 1

    def test_deterministic_seed_reset(self):
        """Test that the same seed produces the same data."""
        results = []
        
        def callback(data, params):
            results.append(data)
            return True
        
        # Run twice with the same params file
        list(streaming_data_generator(str(self.params_file), callback))
        first_run_data = results[0]
        
        results.clear()
        list(streaming_data_generator(str(self.params_file), callback))
        second_run_data = results[0]
        
        # Should be identical
        np.testing.assert_array_equal(first_run_data, second_run_data)

class TestGenerateCorrelatedData:
    def test_shape(self):
        rng = np.random.default_rng(42)
        data = generate_correlated_data(10, 20, 0.5, rng)
        assert data.shape == (10, 20)

    def test_correlation_structure(self):
        """Verify that the generated data has approximately the expected correlation."""
        rng = np.random.default_rng(123)
        n, p, rho = 1000, 100, 0.5
        data = generate_correlated_data(n, p, rho, rng)
        
        # Compute sample correlation of first few columns
        # Theoretical correlation between col i and j is rho^|i-j|
        corr_matrix = np.corrcoef(data.T)
        
        # Check lag 1
        observed_r = np.mean([corr_matrix[i, i+1] for i in range(p-1)])
        # Should be close to rho
        assert abs(observed_r - rho) < 0.1 # Tolerance for sampling noise

class TestGenerateDistributionViolations:
    def test_normal_no_change(self):
        rng = np.random.default_rng(42)
        X = rng.standard_normal((50, 50))
        X_out = generate_distribution_violations(X, 'normal', rng)
        np.testing.assert_array_equal(X, X_out)

    def test_t_dist_heavy_tails(self):
        rng = np.random.default_rng(42)
        X = rng.standard_normal((1000, 100))
        X_out = generate_distribution_violations(X, 't', rng)
        
        # Check that kurtosis is higher (heavy tails)
        from scipy import stats
        kurtosis_orig = stats.kurtosis(X.flatten())
        kurtosis_new = stats.kurtosis(X_out.flatten())
        
        # t-distribution with df=3 has kurtosis 6 (excess kurtosis 3? Actually excess kurtosis is 6 for df=3)
        # Normal has excess kurtosis 0.
        # So kurtosis_new should be significantly larger than kurtosis_orig
        assert kurtosis_new > kurtosis_orig

    def test_skew_normal(self):
        rng = np.random.default_rng(42)
        X = rng.standard_normal((1000, 100))
        X_out = generate_distribution_violations(X, 'skew_normal', rng)
        
        from scipy import stats
        skew_orig = stats.skew(X.flatten())
        skew_new = stats.skew(X_out.flatten())
        
        # Skew normal should have non-zero skewness
        assert abs(skew_new) > 0.1