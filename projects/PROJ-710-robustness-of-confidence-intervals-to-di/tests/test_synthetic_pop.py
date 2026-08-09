"""
Unit tests for synthetic population generation.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.data.synthetic_pop import (
    generate_synthetic_populations,
    _generate_adult_like_population,
    _generate_iris_like_population,
    _generate_wine_quality_like_population
)
from code.config import Config


class TestAdultPopulation:
    def test_adult_generation(self):
        """Test that adult population generation produces correct shape and parameters."""
        n_samples = 10000
        seed = 42
        
        samples, params = _generate_adult_like_population(n_samples, seed)
        
        # Check shape
        assert samples.shape == (n_samples,)
        
        # Check that parameters are present
        assert "true_mean" in params
        assert "true_variance" in params
        assert "distribution_params" in params
        
        # Check that samples are positive (age > 0)
        assert np.all(samples > 0)
        
        # Check that samples are in a reasonable range (17-100)
        assert np.all(samples >= 17)
        assert np.all(samples <= 100)  # Reasonable upper bound
        
        # Check that the empirical mean is close to the true mean
        empirical_mean = np.mean(samples)
        true_mean = params["true_mean"]
        # Allow some tolerance due to sampling variance
        assert abs(empirical_mean - true_mean) < 1.0  # Within 1 year
        
        # Check that the empirical variance is close to the true variance
        empirical_var = np.var(samples)
        true_var = params["true_variance"]
        assert abs(empirical_var - true_var) < 5.0  # Within 5 variance units


class TestIrisPopulation:
    def test_iris_generation(self):
        """Test that iris population generation produces correct shape and parameters."""
        n_samples = 10000
        seed = 42
        
        samples, params = _generate_iris_like_population(n_samples, seed)
        
        # Check shape
        assert samples.shape == (n_samples,)
        
        # Check that parameters are present
        assert "true_mean" in params
        assert "true_variance" in params
        
        # Check that samples are non-negative
        assert np.all(samples >= 0)
        
        # Check that samples are in a reasonable range (0-10 cm)
        assert np.all(samples <= 10)
        
        # Check empirical vs true mean
        empirical_mean = np.mean(samples)
        true_mean = params["true_mean"]
        assert abs(empirical_mean - true_mean) < 0.2  # Within 0.2 cm
        
        # Check empirical vs true variance
        empirical_var = np.var(samples)
        true_var = params["true_variance"]
        assert abs(empirical_var - true_var) < 0.5  # Within 0.5 variance units


class TestWinePopulation:
    def test_wine_generation(self):
        """Test that wine population generation produces correct shape and parameters."""
        n_samples = 10000
        seed = 42
        
        x, x_params, y, y_params = _generate_wine_quality_like_population(n_samples, seed)
        
        # Check shapes
        assert x.shape == (n_samples,)
        assert y.shape == (n_samples,)
        
        # Check that parameters are present
        assert "true_slope" in x_params
        assert "true_intercept" in x_params
        
        # Check that X (alcohol) is in a reasonable range (8-15%)
        assert np.all(x >= 8)
        assert np.all(x <= 15)
        
        # Check that Y (quality) is in a reasonable range (3-9)
        assert np.all(y >= 3)
        assert np.all(y <= 9)
        
        # Check empirical slope (approximate)
        # We can't check exact slope due to noise, but we can check correlation
        correlation = np.corrcoef(x, y)[0, 1]
        assert correlation > 0.3  # Should be positive correlation
        
        # Check that the true slope is positive
        assert x_params["true_slope"] > 0


class TestFullGeneration:
    def test_full_generation(self):
        """Test the full generation function with a small sample size."""
        n_sim = 1000  # Small sample for testing
        seed = 42
        
        ground_truth, populations = generate_synthetic_populations(n_sim, seed)
        
        # Check that all expected datasets are present
        assert "adult" in ground_truth
        assert "iris" in ground_truth
        assert "wine" in ground_truth
        
        # Check that populations are present
        assert "adult" in populations
        assert "iris" in populations
        assert "wine_x" in populations
        assert "wine_y" in populations
        
        # Check that populations have the correct size
        assert populations["adult"].shape == (n_sim,)
        assert populations["iris"].shape == (n_sim,)
        assert populations["wine_x"].shape == (n_sim,)
        assert populations["wine_y"].shape == (n_sim,)
        
        # Check that ground truth has required fields
        for dataset in ["adult", "iris", "wine"]:
            assert "true_mean" in ground_truth[dataset] or "true_slope" in ground_truth[dataset]
            assert "distribution_params" in ground_truth[dataset]
            assert "sample_size" in ground_truth[dataset]
            assert ground_truth[dataset]["sample_size"] == n_sim


    def test_ground_truth_serialization(self):
        """Test that ground truth can be serialized to JSON."""
        n_sim = 1000
        seed = 42
        
        ground_truth, _ = generate_synthetic_populations(n_sim, seed)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            # Convert to serializable format
            def convert_to_serializable(obj):
                if isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, dict):
                    return {k: convert_to_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_to_serializable(i) for i in obj]
                return obj
            
            serializable_gt = convert_to_serializable(ground_truth)
            
            with open(temp_path, 'w') as f:
                json.dump(serializable_gt, f)
            
            # Read back and verify
            with open(temp_path, 'r') as f:
                loaded_gt = json.load(f)
            
            # Check that all keys are preserved
            assert set(loaded_gt.keys()) == set(ground_truth.keys())
            
            # Check that numeric values are preserved
            for dataset in loaded_gt:
                if "true_mean" in loaded_gt[dataset]:
                    assert abs(loaded_gt[dataset]["true_mean"] - ground_truth[dataset]["true_mean"]) < 1e-6
        finally:
            if temp_path.exists():
                os.unlink(temp_path)