import pytest
import numpy as np
import pandas as pd
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

# Import the functions to test
from simulation import (
    fit_negative_binomial,
    generate_nb_null_model,
    generate_permutation_null_model,
    run_monte_carlo_chunked,
    save_simulation_results,
    StatisticalModelError
)

class TestFitNegativeBinomial:
    def test_fit_with_valid_data(self):
        """Test fitting with valid non-negative integer data."""
        # Create synthetic data that resembles a negative binomial distribution
        rng = np.random.default_rng(42)
        data = rng.negative_binomial(10, 0.5, size=1000)
        
        n, p = fit_negative_binomial(data)
        
        assert n > 0
        assert 0 < p <= 1
        assert isinstance(n, float)
        assert isinstance(p, float)

    def test_fit_with_empty_data(self):
        """Test fitting with empty data raises error."""
        data = np.array([])
        with pytest.raises(StatisticalModelError):
            fit_negative_binomial(data)

    def test_fit_with_negative_data(self):
        """Test fitting with negative data filters them out."""
        data = np.array([-5, -2, 0, 1, 3, 5])
        # Should filter out negatives and fit on [0, 1, 3, 5]
        n, p = fit_negative_binomial(data)
        assert n > 0
        assert 0 < p <= 1

class TestGenerateNbNullModel:
    def test_generate_samples(self):
        """Test that the model generates the correct number of samples."""
        n, p = 10, 0.5
        size = 100
        seed = 42
        
        samples = generate_nb_null_model(n, p, size, seed)
        
        assert len(samples) == size
        assert all(samples >= 0)  # Negative binomial produces non-negative integers

    def test_reproducibility(self):
        """Test that the same seed produces the same results."""
        n, p = 10, 0.5
        size = 100
        seed = 42
        
        samples1 = generate_nb_null_model(n, p, size, seed)
        samples2 = generate_nb_null_model(n, p, size, seed)
        
        np.testing.assert_array_equal(samples1, samples2)

class TestGeneratePermutationNullModel:
    def test_permutation_samples(self):
        """Test permutation model generates correct number of samples."""
        observed = np.array([1, 2, 3, 4, 5])
        n_permutations = 10
        seed = 42
        
        samples = generate_permutation_null_model(observed, n_permutations, seed)
        
        assert len(samples) == n_permutations
        # All samples should be from the observed set
        assert all(s in observed for s in samples)

    def test_reproducibility(self):
        """Test reproducibility of permutation model."""
        observed = np.array([1, 2, 3, 4, 5])
        n_permutations = 10
        seed = 42
        
        samples1 = generate_permutation_null_model(observed, n_permutations, seed)
        samples2 = generate_permutation_null_model(observed, n_permutations, seed)
        
        np.testing.assert_array_equal(samples1, samples2)

class TestRunMonteCarloChunked:
    def test_chunked_processing(self):
        """Test that chunked processing produces results."""
        # Create mock data
        data = pd.DataFrame({
            'discrepancy_abs': np.random.poisson(5, 100)
        })
        
        results = run_monte_carlo_chunked(
            data=data,
            n_iterations=100,
            chunk_size=20,
            seed=42,
            model_type="negative_binomial"
        )
        
        assert isinstance(results, list)
        assert len(results) == 5  # 100 / 20 = 5 chunks
        
        # Check structure of first result
        first_chunk = results[0]
        assert 'chunk_id' in first_chunk
        assert 'mean' in first_chunk
        assert 'std' in first_chunk
        assert 'model_type' in first_chunk

    def test_fallback_to_permutation(self):
        """Test that the function falls back to permutation if NB fit fails."""
        # Create data that might cause NB fit to fail (e.g., all zeros)
        data = pd.DataFrame({
            'discrepancy_abs': np.zeros(100)
        })
        
        # This should not raise an error but switch to permutation
        results = run_monte_carlo_chunked(
            data=data,
            n_iterations=50,
            chunk_size=10,
            seed=42,
            model_type="negative_binomial"
        )
        
        assert len(results) > 0
        # Check that at least one chunk used permutation
        assert any(r['model_type'] == 'permutation' for r in results)

    def test_invalid_iterations(self):
        """Test that invalid iterations raise errors."""
        data = pd.DataFrame({'discrepancy_abs': [1, 2, 3]})
        
        with pytest.raises(ValueError):
            run_monte_carlo_chunked(data, n_iterations=0)
        
        with pytest.raises(ValueError):
            run_monte_carlo_chunked(data, n_iterations=-10)

    def test_chunk_size_adjustment(self):
        """Test that chunk_size is adjusted if larger than n_iterations."""
        data = pd.DataFrame({
            'discrepancy_abs': np.random.poisson(5, 100)
        })
        
        # Request 50 iterations with chunk_size=100
        results = run_monte_carlo_chunked(
            data=data,
            n_iterations=50,
            chunk_size=100,
            seed=42,
            model_type="negative_binomial"
        )
        
        assert len(results) == 1  # Should be one chunk of 50

class TestSaveSimulationResults:
    def test_save_to_json(self):
        """Test saving results to a JSON file."""
        results = [
            {'chunk_id': 0, 'mean': 5.0, 'std': 1.0},
            {'chunk_id': 1, 'mean': 5.1, 'std': 1.1}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            save_simulation_results(results, output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert len(loaded) == 2
            assert loaded[0]['chunk_id'] == 0
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_numpy_type_conversion(self):
        """Test that numpy types are converted to native Python types."""
        import numpy as np
        
        results = [
            {
                'chunk_id': np.int64(0),
                'mean': np.float64(5.0),
                'nb_params': {
                    'n': np.float64(10.0),
                    'p': np.float64(0.5)
                }
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name
        
        try:
            save_simulation_results(results, output_path)
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            # Verify types are native Python
            assert isinstance(loaded[0]['chunk_id'], int)
            assert isinstance(loaded[0]['mean'], float)
            assert isinstance(loaded[0]['nb_params']['n'], float)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
