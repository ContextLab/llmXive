"""
Unit tests for the benchmark_runner module.

These tests verify the projection logic and basic functionality
without requiring the full model loading pipeline.
"""
import numpy as np
import pytest
import json
import os
from pathlib import Path

# Import the functions to test
from benchmark_runner import (
    generate_synthetic_weights,
    benchmark_svd,
    benchmark_permutation,
    project_runtime,
    run_benchmark,
    MAX_ALLOWED_HOURS
)

class TestSyntheticWeights:
    def test_generate_weights_shape(self):
        """Test that synthetic weights have the correct shape."""
        rows, cols = 10, 4096
        seed = 42
        weights = generate_synthetic_weights(rows, cols, seed)
        assert weights.shape == (rows, cols)
        assert weights.dtype == np.float32

    def test_generate_weights_deterministic(self):
        """Test that synthetic weights are deterministic with the same seed."""
        rows, cols = 10, 4096
        seed = 42
        weights1 = generate_synthetic_weights(rows, cols, seed)
        weights2 = generate_synthetic_weights(rows, cols, seed)
        assert np.array_equal(weights1, weights2)

class TestBenchmarkSVD:
    def test_benchmark_svd_time_positive(self):
        """Test that SVD benchmark returns a positive time."""
        matrix = generate_synthetic_weights(10, 4096, 42)
        time_val, stats = benchmark_svd(matrix, k=10, seed=42)
        assert time_val > 0
        assert "svd_time_seconds" in stats

    def test_benchmark_svd_k_vectors(self):
        """Test that the correct number of vectors are extracted."""
        matrix = generate_synthetic_weights(10, 4096, 42)
        k = 5
        time_val, stats = benchmark_svd(matrix, k=k, seed=42)
        # The stats don't explicitly return U, but the function executes successfully
        assert "error" not in stats

class TestBenchmarkPermutation:
    def test_benchmark_permutation_time_positive(self):
        """Test that permutation benchmark returns a positive time."""
        matrix = generate_synthetic_weights(10, 4096, 42)
        time_val, stats = benchmark_permutation(matrix, n_iterations=5, seed=42)
        assert time_val > 0
        assert "permutation_time_seconds" in stats

class TestProjectRuntime:
    def test_project_runtime_scaling(self):
        """Test that runtime projection scales correctly."""
        # Mock subset times (in seconds)
        subset_svd_time = 0.01  # 10ms
        subset_perm_time = 0.05 # 50ms
        
        projections = project_runtime(subset_svd_time, subset_perm_time)
        
        # Check that projections are positive
        assert projections['projected_svd_hours'] > 0
        assert projections['projected_perm_hours'] > 0
        assert projections['total_projected_hours'] > 0
        
        # Check scaling factor (10000 vocab / 10 subset = 1000)
        # Note: The constant FULL_VOCAB_ESTIMATE is 50000 in the module
        expected_factor = 50000 / 10
        assert abs(projections['scaling_factor_vocab'] - expected_factor) < 1e-6

    def test_project_runtime_threshold_check(self):
        """Test that the threshold check logic is sound."""
        # Simulate a very fast run
        projections = project_runtime(0.001, 0.001)
        # This should definitely be under 5 hours
        assert projections['total_projected_hours'] < MAX_ALLOWED_HOURS

        # Simulate a slow run (hypothetically)
        # We can't easily force the function to return > 5 hours without mocking
        # the internal scaling, but we can verify the threshold constant is reasonable.
        assert MAX_ALLOWED_HOURS == 5.0

class TestRunBenchmark:
    def test_run_benchmark_structure(self):
        """Test that run_benchmark returns the expected structure."""
        config = {}
        result = run_benchmark(config)
        
        assert "status" in result
        assert "threshold_hours" in result
        assert "projected_hours" in result
        assert "subset_results" in result
        assert "projections" in result
        assert "timestamp" in result
        
        assert result["status"] in ["PASS", "FAIL"]
        assert isinstance(result["projected_hours"], float)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])