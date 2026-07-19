"""
Unit tests for feature calculation logic in code/features.py.

This module includes a synthetic data generator for testing purposes only.
The generated data strictly adheres to the schema defined in 
contracts/dataset.schema.yaml to ensure test validity.
"""

import pytest
import numpy as np
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from features import (
    calculate_variance_and_range,
    calculate_entropy,
    calculate_skewness_and_kurtosis,
    calculate_per_sample_stats,
    calculate_global_entanglement_score,
    calculate_dimensional_fidelity_loss
)

# ============================================================================
# Synthetic Data Generator for Testing
# ============================================================================

def generate_synthetic_dataset(
    num_samples: int = 10, 
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Generate a small, fake dataset adhering to contracts/dataset.schema.yaml.
    
    This generator creates numpy arrays and structured data to test feature 
    calculation logic (variance, eigenvalue, entropy, etc.) without requiring 
    the full Z-Reward dataset.
    
    Args:
        num_samples: Number of synthetic samples to generate.
        seed: Random seed for reproducibility.
    
    Returns:
        List of dictionaries, each representing a sample with:
        - sample_id (str)
        - prompt (str)
        - teacher_logits (dict with 4 float keys)
        - student_scalar (float)
        - human_annotations (dict with 4 float keys, 0-1 range)
        - metadata (dict with primary_quality_dimension)
    """
    rng = np.random.default_rng(seed)
    
    dimensions = ["alignment", "realism", "aesthetics", "plausibility"]
    data = []
    
    for i in range(num_samples):
        # Generate teacher logits (real-valued, unbounded)
        teacher_logits = {
            dim: rng.normal(loc=0.0, scale=1.0) for dim in dimensions
        }
        
        # Generate student scalar (real-valued)
        student_scalar = rng.normal(loc=0.5, scale=0.2)
        
        # Generate human annotations (bounded 0-1)
        human_annotations = {
            dim: rng.uniform(0.0, 1.0) for dim in dimensions
        }
        
        # Select primary quality dimension randomly
        primary_dim = rng.choice(dimensions)
        
        sample = {
            "sample_id": f"sample_{i:04d}",
            "prompt": f"Test prompt for sample {i}",
            "teacher_logits": teacher_logits,
            "student_scalar": student_scalar,
            "human_annotations": human_annotations,
            "metadata": {
                "primary_quality_dimension": primary_dim
            }
        }
        data.append(sample)
    
    return data

def generate_synthetic_features_data(
    num_samples: int = 20,
    seed: int = 123
) -> np.ndarray:
    """
    Generate a 2D numpy array representing teacher logits for multiple samples.
    
    This is used specifically for testing global entanglement score (eigenvalue)
    calculations where we need a matrix of shape (num_samples, 4).
    
    Args:
        num_samples: Number of samples.
        seed: Random seed.
    
    Returns:
        np.ndarray of shape (num_samples, 4) with float values.
    """
    rng = np.random.default_rng(seed)
    return rng.normal(loc=0.0, scale=1.5, size=(num_samples, 4))

# ============================================================================
# Tests
# ============================================================================

class TestSyntheticDataGeneration:
    """Tests for the synthetic data generator itself."""

    def test_schema_compliance(self):
        """Verify generated data matches the required schema."""
        data = generate_synthetic_dataset(num_samples=5, seed=42)
        
        assert len(data) == 5
        required_keys = ["sample_id", "prompt", "teacher_logits", 
                       "student_scalar", "human_annotations", "metadata"]
        
        for sample in data:
            for key in required_keys:
                assert key in sample, f"Missing key: {key}"
            
            # Check teacher_logits structure
            dims = ["alignment", "realism", "aesthetics", "plausibility"]
            for dim in dims:
                assert dim in sample["teacher_logits"]
                assert isinstance(sample["teacher_logits"][dim], float)
            
            # Check human_annotations structure and range
            for dim in dims:
                assert dim in sample["human_annotations"]
                val = sample["human_annotations"][dim]
                assert 0.0 <= val <= 1.0, f"Annotation out of range: {val}"
            
            # Check metadata
            assert "primary_quality_dimension" in sample["metadata"]
            assert sample["metadata"]["primary_quality_dimension"] in dims

    def test_reproducibility(self):
        """Verify that same seed produces same data."""
        data1 = generate_synthetic_dataset(num_samples=3, seed=999)
        data2 = generate_synthetic_dataset(num_samples=3, seed=999)
        
        assert data1 == data2

    def test_feature_matrix_generation(self):
        """Test the numpy array generator for entanglement calculations."""
        matrix = generate_synthetic_features_data(num_samples=10, seed=42)
        
        assert matrix.shape == (10, 4)
        assert matrix.dtype in [np.float32, np.float64]
        assert not np.any(np.isnan(matrix))

class TestVarianceAndRange:
    """Tests for variance and range calculations."""

    def test_variance_calculation(self):
        """Test variance calculation on known data."""
        # Create a simple 2D array: 3 samples, 2 dimensions
        data = np.array([
            [1.0, 10.0],
            [2.0, 20.0],
            [3.0, 30.0]
        ])
        
        variances, ranges = calculate_variance_and_range(data)
        
        # Expected variance for [1, 2, 3] is 1.0 (population) or 1.0 (sample with ddof=0)
        # Using numpy default (ddof=0)
        expected_var = np.var(data, axis=0)
        expected_range = np.ptp(data, axis=0)
        
        np.testing.assert_array_almost_equal(variances, expected_var)
        np.testing.assert_array_almost_equal(ranges, expected_range)

    def test_zero_variance_handling(self):
        """Test that zero variance is handled correctly."""
        data = np.array([
            [5.0, 10.0],
            [5.0, 10.0],
            [5.0, 10.0]
        ])
        
        variances, ranges = calculate_variance_and_range(data)
        
        assert variances[0] == 0.0
        assert ranges[0] == 0.0

class TestEntropy:
    """Tests for entropy calculations."""

    def test_entropy_calculation(self):
        """Test entropy calculation on a known distribution."""
        # Normalize data to sum to 1 (probability distribution)
        logits = np.array([1.0, 2.0, 3.0, 4.0])
        probs = np.exp(logits) / np.sum(np.exp(logits))
        
        entropy = calculate_entropy(probs)
        
        # Verify it's a positive value
        assert entropy >= 0

    def test_zero_entropy(self):
        """Test entropy when distribution is deterministic."""
        # One-hot vector (deterministic)
        probs = np.array([1.0, 0.0, 0.0, 0.0])
        entropy = calculate_entropy(probs)
        
        # Entropy of deterministic distribution should be 0
        assert entropy == 0.0

class TestSkewnessAndKurtosis:
    """Tests for skewness and kurtosis."""

    def test_normal_distribution(self):
        """Test that normal distribution has skew ~0 and kurtosis ~3."""
        rng = np.random.default_rng(42)
        data = rng.normal(loc=0, scale=1, size=10000)
        
        skew, kurt = calculate_skewness_and_kurtosis(data)
        
        # Allow some tolerance due to sampling
        assert abs(skew) < 0.2
        assert 2.5 < kurt < 3.5

class TestGlobalEntanglementScore:
    """Tests for global entanglement score (eigenvalue) calculation."""

    def test_eigenvalue_calculation(self):
        """Test that eigenvalue is calculated correctly."""
        # Create a matrix with known structure
        # If dimensions are perfectly correlated, max eigenvalue = sum of variances
        data = np.array([
            [1.0, 1.0, 1.0, 1.0],
            [2.0, 2.0, 2.0, 2.0],
            [3.0, 3.0, 3.0, 3.0],
            [4.0, 4.0, 4.0, 4.0]
        ])
        
        eigenvalue = calculate_global_entanglement_score(data)
        
        # The eigenvalue should be positive
        assert eigenvalue > 0

    def test_synthetic_data_integration(self):
        """Test using the synthetic data generator."""
        synthetic_data = generate_synthetic_features_data(num_samples=50, seed=42)
        
        eigenvalue = calculate_global_entanglement_score(synthetic_data)
        
        assert isinstance(eigenvalue, (float, np.floating))
        assert eigenvalue >= 0

class TestDimensionalFidelityLoss:
    """Tests for dimensional fidelity loss calculation."""

    def test_fidelity_loss_calculation(self):
        """Test fidelity loss for a single sample."""
        # Create a single sample
        sample = generate_synthetic_dataset(num_samples=1, seed=42)[0]
        
        # Extract the primary dimension
        primary_dim = sample["metadata"]["primary_quality_dimension"]
        
        # Calculate expected loss manually
        student_score = sample["student_scalar"]
        human_score = sample["human_annotations"][primary_dim]
        expected_loss = abs(student_score - human_score)
        
        # Use the function
        calculated_loss = calculate_dimensional_fidelity_loss(sample)
        
        assert np.isclose(calculated_loss, expected_loss)

    def test_fidelity_loss_with_synthetic_batch(self):
        """Test fidelity loss on a batch of synthetic data."""
        data = generate_synthetic_dataset(num_samples=10, seed=123)
        
        losses = []
        for sample in data:
            loss = calculate_dimensional_fidelity_loss(sample)
            losses.append(loss)
        
        # All losses should be non-negative
        assert all(l >= 0 for l in losses)
        assert len(losses) == 10

class TestPerSampleStats:
    """Tests for per-sample statistics calculation."""

    def test_per_sample_stats_structure(self):
        """Test that per-sample stats return correct structure."""
        data = generate_synthetic_features_data(num_samples=5, seed=42)
        
        stats = calculate_per_sample_stats(data)
        
        # Should return a list of dicts
        assert isinstance(stats, list)
        assert len(stats) == 5
        
        # Check structure of first item
        first = stats[0]
        assert "variance" in first
        assert "entropy" in first
        assert "skewness" in first
        assert "kurtosis" in first
        assert "range" in first

if __name__ == "__main__":
    pytest.main([__file__, "-v"])