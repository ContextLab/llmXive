"""
Unit tests for the simulation module (T013a).

Tests for:
- generate_synthetic_dataset
- generate_null_hypothesis_dataset
- Deterministic output with fixed seeds
"""
import os
import json
import tempfile
from pathlib import Path
import pytest

import numpy as np
import pandas as pd

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))
from simulate import (
    generate_synthetic_dataset,
    generate_null_hypothesis_dataset,
    load_config,
    determine_iterations
)


class TestGenerateSyntheticDataset:
    """Tests for generate_synthetic_dataset function."""

    def test_synthetic_data_shape(self):
        """Test that generated data has correct shape."""
        n_samples = 100
        n_groups = 2
        result = generate_synthetic_dataset(n_samples=n_samples, n_groups=n_groups, seed=42)
        
        assert 'data' in result
        assert 'ground_truth' in result
        assert isinstance(result['data'], pd.DataFrame)
        assert result['data'].shape == (n_samples, n_groups)

    def test_ground_truth_type(self):
        """Test that ground truth type is correctly set."""
        result = generate_synthetic_dataset(n_samples=100, seed=42)
        
        assert result['ground_truth']['type'] == 'population_parameters'

    def test_ground_truth_parameters(self):
        """Test that ground truth parameters are correctly stored."""
        mean = 5.0
        std = 2.0
        n_samples = 200
        n_groups = 3
        
        result = generate_synthetic_dataset(
            n_samples=n_samples,
            n_groups=n_groups,
            mean=mean,
            std=std,
            seed=42
        )
        
        gt = result['ground_truth']
        assert gt['mean'] == mean
        assert gt['std'] == std
        assert gt['n_samples'] == n_samples
        assert gt['n_groups'] == n_groups

    def test_deterministic_output(self):
        """Test that same seed produces same output."""
        result1 = generate_synthetic_dataset(n_samples=100, seed=42)
        result2 = generate_synthetic_dataset(n_samples=100, seed=42)
        
        # Compare dataframes
        pd.testing.assert_frame_equal(result1['data'], result2['data'])

    def test_sample_mean_approximates_population_mean(self):
        """Test that sample mean is close to population mean (statistical test)."""
        mean = 10.0
        std = 1.0
        n_samples = 10000  # Large sample for better approximation
        
        result = generate_synthetic_dataset(
            n_samples=n_samples,
            mean=mean,
            std=std,
            seed=42
        )
        
        # Calculate overall sample mean
        sample_mean = result['data'].mean().mean()
        
        # With large n, sample mean should be close to population mean
        # Allow for some statistical variation
        assert abs(sample_mean - mean) < 0.1


class TestGenerateNullHypothesisDataset:
    """Tests for generate_null_hypothesis_dataset function."""

    def test_null_data_shape(self):
        """Test that generated null data has correct shape."""
        n_samples = 100
        n_groups = 2
        result = generate_null_hypothesis_dataset(n_samples=n_samples, n_groups=n_groups, seed=42)
        
        assert 'data' in result
        assert 'ground_truth' in result
        assert isinstance(result['data'], pd.DataFrame)
        assert result['data'].shape == (n_samples, n_groups)

    def test_null_ground_truth_type(self):
        """Test that ground truth type is correctly set for null hypothesis."""
        result = generate_null_hypothesis_dataset(n_samples=100, seed=42)
        
        assert result['ground_truth']['type'] == 'permutation'

    def test_null_deterministic_output(self):
        """Test that same seed produces same null output."""
        result1 = generate_null_hypothesis_dataset(n_samples=100, seed=42)
        result2 = generate_null_hypothesis_dataset(n_samples=100, seed=42)
        
        pd.testing.assert_frame_equal(result1['data'], result2['data'])

    def test_null_means_approximate_zero(self):
        """Test that null hypothesis data has means close to zero."""
        n_samples = 10000
        
        result = generate_null_hypothesis_dataset(n_samples=n_samples, seed=42)
        
        group_means = result['data'].mean()
        # All group means should be close to 0
        for mean in group_means:
            assert abs(mean) < 0.1


class TestDetermineIterations:
    """Tests for determine_iterations function."""

    def test_iterations_within_bounds(self):
        """Test that returned iterations are within valid bounds."""
        iterations = determine_iterations(target_se=0.005, max_iterations=1000)
        assert 0 < iterations <= 1000

    def test_iterations_respects_max(self):
        """Test that iterations don't exceed max_iterations."""
        iterations = determine_iterations(target_se=0.001, max_iterations=100)
        assert iterations <= 100

    def test_iterations_decreases_with_larger_target_se(self):
        """Test that larger target SE requires fewer iterations."""
        iterations_strict = determine_iterations(target_se=0.001, max_iterations=10000)
        iterations_loose = determine_iterations(target_se=0.01, max_iterations=10000)
        
        assert iterations_strict > iterations_loose
