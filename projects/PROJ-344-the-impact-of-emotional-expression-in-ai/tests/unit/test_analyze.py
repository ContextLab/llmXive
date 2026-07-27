"""
Unit tests for ordinal regression model fitting in analyze.py.

Tests:
- Ordinal regression with synthetic metadata
- Model convergence
- Result structure validation
"""
import pytest
import numpy as np
import pandas as pd
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analyze import run_ordinal_regression, load_consistency_scores

class TestOrdinalRegression:
    """Tests for ordinal regression functionality."""

    @pytest.fixture
    def synthetic_data(self):
        """Create synthetic dataset for testing ordinal regression."""
        np.random.seed(42)
        n_samples = 100
        
        # Generate synthetic data
        data = {
            'interaction_id': range(n_samples),
            'consistency_score': np.random.uniform(-1, 1, n_samples),
            'trust_score': np.random.choice([1, 2, 3, 4, 5], n_samples),
            'avatar_type': np.random.choice(['neutral', 'happy', 'sad', 'angry'], n_samples),
            'duration': np.random.uniform(10, 120, n_samples),
            'difficulty': np.random.choice([1, 2, 3, 4, 5], n_samples)
        }
        
        return pd.DataFrame(data)

    def test_ordinal_regression_runs(self, synthetic_data):
        """Test that ordinal regression runs without errors."""
        results = run_ordinal_regression(synthetic_data)
        
        assert isinstance(results, dict)
        assert 'coefficients' in results
        assert 'p_values' in results
        assert 'pseudo_r_squared' in results
        assert 'model_converged' in results

    def test_ordinal_regression_coefficients_structure(self, synthetic_data):
        """Test that coefficients contain expected variables."""
        results = run_ordinal_regression(synthetic_data)
        
        coeffs = results['coefficients']
        
        # Should have intercept and main variables
        assert 'const' in coeffs
        assert 'consistency_score' in coeffs
        assert 'duration' in coeffs
        assert 'difficulty' in coeffs

    def test_ordinal_regression_pseudo_r_squared(self, synthetic_data):
        """Test that pseudo R-squared is within reasonable range."""
        results = run_ordinal_regression(synthetic_data)
        
        pseudo_r2 = results['pseudo_r_squared']
        
        # Pseudo R-squared should be between 0 and 1
        assert 0 <= pseudo_r2 <= 1

    def test_ordinal_regression_with_small_sample(self):
        """Test ordinal regression with minimal sample size."""
        np.random.seed(42)
        n_samples = 15
        
        data = {
            'interaction_id': range(n_samples),
            'consistency_score': np.random.uniform(-1, 1, n_samples),
            'trust_score': np.random.choice([1, 2, 3, 4, 5], n_samples),
            'avatar_type': np.random.choice(['neutral', 'happy'], n_samples),
            'duration': np.random.uniform(10, 120, n_samples),
            'difficulty': np.random.choice([1, 2, 3, 4, 5], n_samples)
        }
        
        df = pd.DataFrame(data)
        
        # Should not raise error with minimum sample
        results = run_ordinal_regression(df)
        
        assert isinstance(results, dict)
        assert results['n_observations'] == n_samples

    def test_ordinal_regression_missing_data_handling(self):
        """Test that ordinal regression handles missing data correctly."""
        np.random.seed(42)
        n_samples = 50
        
        data = {
            'interaction_id': range(n_samples),
            'consistency_score': np.random.uniform(-1, 1, n_samples),
            'trust_score': np.random.choice([1, 2, 3, 4, 5], n_samples),
            'avatar_type': np.random.choice(['neutral', 'happy', 'sad'], n_samples),
            'duration': np.random.uniform(10, 120, n_samples),
            'difficulty': np.random.choice([1, 2, 3, 4, 5], n_samples)
        }
        
        df = pd.DataFrame(data)
        
        # Introduce some NaN values
        df.loc[0, 'consistency_score'] = np.nan
        df.loc[1, 'trust_score'] = np.nan
        df.loc[2, 'avatar_type'] = np.nan
        
        # Should handle missing data by dropping rows
        results = run_ordinal_regression(df)
        
        # Should have fewer observations than original
        assert results['n_observations'] < n_samples

    def test_ordinal_regression_convergence(self, synthetic_data):
        """Test that model converges on synthetic data."""
        results = run_ordinal_regression(synthetic_data)
        
        # Model should converge on reasonable synthetic data
        assert results['model_converged'] is True

    def test_ordinal_regression_output_statistics(self, synthetic_data):
        """Test that all required statistics are present in output."""
        results = run_ordinal_regression(synthetic_data)
        
        required_keys = [
            'coefficients', 'p_values', 'pseudo_r_squared',
            'log_likelihood', 'aic', 'bic', 'n_observations',
            'n_parameters', 'model_converged'
        ]
        
        for key in required_keys:
            assert key in results, f"Missing required key: {key}"

    def test_ordinal_regression_p_values_type(self, synthetic_data):
        """Test that p-values are numeric and in valid range."""
        results = run_ordinal_regression(synthetic_data)
        
        p_values = results['p_values']
        
        for var, p in p_values.items():
            assert isinstance(p, (int, float)), f"P-value for {var} is not numeric"
            assert 0 <= p <= 1, f"P-value for {var} out of range: {p}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])