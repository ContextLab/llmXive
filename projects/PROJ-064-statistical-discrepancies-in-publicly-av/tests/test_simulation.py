import pytest
import numpy as np
import pandas as pd
import json
import os
import tempfile
from scipy import stats

# Import the functions to test
from code.simulation import (
    fit_negative_binomial,
    generate_nb_null_model,
    generate_permutation_null_model,
    run_monte_carlo_chunked,
    save_simulation_results,
    main
)
from code.exceptions import StatisticalModelError

class TestNegativeBinomialFit:
    def test_fit_with_positive_data(self):
        """Test NB fit with standard positive data"""
        # Generate synthetic data that looks like NB
        rng = np.random.default_rng(42)
        n, p = 10, 0.5
        synthetic_data = rng.negative_binomial(n, p, 10000)
        
        mu, alpha = fit_negative_binomial(synthetic_data)
        
        assert mu > 0, "mu should be positive"
        assert alpha > 0, "alpha should be positive"
        # Check if parameters are reasonable (mu should be close to n*(1-p)/p = 10)
        assert 5 < mu < 20, f"mu={mu} is outside expected range"
        assert 0.1 < alpha < 100, f"alpha={alpha} is outside expected range"

    def test_fit_with_zero_variance(self):
        """Test NB fit with constant data (zero variance)"""
        data = np.array([5.0] * 100)
        mu, alpha = fit_negative_binomial(data)
        
        # Should return large alpha (Poisson-like)
        assert alpha > 1e5, "alpha should be very large for zero variance data"
        assert mu == 5.0, "mu should be 5.0"

    def test_fit_with_negative_data_fails(self):
        """Test that NB fit fails if all data is negative"""
        data = np.array([-1.0, -2.0, -3.0])
        with pytest.raises(ValueError):
            fit_negative_binomial(data)

    def test_fit_with_mixed_data(self):
        """Test NB fit with mixed positive/negative data (should filter negatives)"""
        data = np.array([-5.0, -1.0, 2.0, 3.0, 4.0, 5.0])
        mu, alpha = fit_negative_binomial(data)
        
        # Should only use positive values: [2, 3, 4, 5] -> median = 3.5
        assert mu > 0, "mu should be positive"
        assert alpha > 0, "alpha should be positive"

class TestNullModelGeneration:
    def test_nb_generation(self):
        """Test NB null model generation"""
        mu, alpha = 5.0, 2.0
        rng = np.random.default_rng(42)
        samples = generate_nb_null_model(mu, alpha, 1000, rng)
        
        assert len(samples) == 1000
        assert np.all(samples >= 0), "NB samples should be non-negative"
        
        # Check mean roughly matches mu
        assert 2 < np.mean(samples) < 10, "Mean should be in reasonable range"

    def test_permutation_generation(self):
        """Test Permutation null model generation"""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        rng = np.random.default_rng(42)
        samples = generate_permutation_null_model(data, 1000, rng)
        
        assert len(samples) == 1000
        # All samples should be from the original set
        assert set(samples).issubset(set(data)), "Permutation samples must be from original data"

class TestMonteCarloChunked:
    def test_chunked_equivalence(self):
        """Test that chunked processing yields equivalent results to single batch"""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        seed = 42
        iterations = 1000
        
        # Run chunked
        results_chunked = run_monte_carlo_chunked(
            observed_data=data,
            iterations=iterations,
            seed=seed,
            chunk_size=100,
            model_type="perm"
        )
        
        # Run single batch
        results_single = run_monte_carlo_chunked(
            observed_data=data,
            iterations=iterations,
            seed=seed,
            chunk_size=iterations,
            model_type="perm"
        )
        
        # Compare distributions using KS test
        ks_stat, p_value = stats.ks_2samp(results_chunked["distribution"], results_single["distribution"])
        assert p_value > 0.05, "Chunked and single batch results should be statistically equivalent"

    def test_nb_fallback_to_perm(self):
        """Test that NB model falls back to Permutation if fit fails"""
        # Create data that will fail NB fit (all negative)
        data = np.array([-1.0, -2.0, -3.0, -4.0, -5.0])
        
        results = run_monte_carlo_chunked(
            observed_data=data,
            iterations=100,
            seed=42,
            chunk_size=10,
            model_type="nb"
        )
        
        assert results["model_type"] == "perm", "Should fallback to permutation model"

class TestSaveSimulationResults:
    def test_save_and_load(self):
        """Test saving and loading simulation results"""
        results = {
            "distribution": np.array([1.0, 2.0, 3.0]),
            "model_type": "perm",
            "iterations": 100,
            "seed": 42
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            save_simulation_results(results, temp_path)
            
            with open(temp_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded["model_type"] == "perm"
            assert loaded["iterations"] == 100
            assert len(loaded["distribution"]) == 3
        finally:
            os.unlink(temp_path)

class TestMain:
    def test_main_with_csv_input(self):
        """Test main function with CSV input"""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("discrepancy_abs\n1.0\n2.0\n3.0\n4.0\n5.0\n")
            input_path = f.name
        
        output_path = tempfile.mktemp(suffix='.json')
        
        try:
            # Simulate command line args
            import sys
            original_argv = sys.argv
            sys.argv = ['simulation.py', '--input', input_path, '--output', output_path, '--iterations', '100', '--seed', '42']
            
            main()
            
            assert os.path.exists(output_path), "Output file should be created"
            
            with open(output_path, 'r') as f:
                results = json.load(f)
            
            assert "distribution" in results
            assert len(results["distribution"]) == 100
        finally:
            sys.argv = original_argv
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
