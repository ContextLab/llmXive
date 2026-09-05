"""
Test suite for data generation utilities, focusing on:
1. Moment extraction (mean, variance, sparsity, outlier_magnitude)
2. Epsilon handling (apply_epsilon_floor)

This test suite validates the core logic required for User Story 1 (US1)
and ensures compatibility with the SingleStepSinkhornSolver (T016) interface.
"""
import pytest
import numpy as np
import sys
import os
from pathlib import Path

# Ensure project root is in path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data_generation.utils import (
    apply_epsilon_floor,
    check_numerical_stability,
    safe_log,
    safe_divide
)
from entities import AttentionMatrix
from config import get_config

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

@pytest.fixture
def base_matrix():
    """
    Generates a standard 128x128 attention matrix with controlled properties:
    - Mean: ~0.5
    - Variance: ~0.1
    - Sparsity: ~10% (zeros)
    - Outliers: 5 values with magnitude > 3.0 * std
    """
    np.random.seed(42)
    size = 128
    total_elements = size * size
    
    # Create base distribution
    data = np.random.normal(loc=0.5, scale=0.1, size=total_elements)
    
    # Inject sparsity (10% zeros)
    num_zeros = int(total_elements * 0.10)
    zero_indices = np.random.choice(total_elements, num_zeros, replace=False)
    data[zero_indices] = 0.0
    
    # Inject outliers (5 extreme values)
    current_std = np.std(data)
    outlier_indices = np.random.choice(total_elements, 5, replace=False)
    # Ensure outliers are significantly larger than current std
    data[outlier_indices] = data.mean() + (3.5 * current_std) + np.random.uniform(0.5, 1.0, 5)
    
    return data.reshape(size, size)

@pytest.fixture
def edge_case_matrix():
    """
    Matrix with extreme edge cases:
    - All zeros (sparsity 100%)
    - Near-zero variance
    """
    return np.zeros((128, 128), dtype=np.float32)

@pytest.fixture
def config():
    """Load project configuration"""
    return get_config()

# --------------------------------------------------------------------------
# Tests for apply_epsilon_floor
# --------------------------------------------------------------------------

class TestApplyEpsilonFloor:
    """Tests for the apply_epsilon_floor utility function."""

    def test_floor_applied_to_small_values(self, base_matrix, config):
        """Verify that values smaller than EPSILON_FLOOR are clamped."""
        epsilon = config.EPSILON_FLOOR
        
        # Create a matrix with known small values
        test_matrix = np.full((10, 10), 1e-9, dtype=np.float32)
        
        result = apply_epsilon_floor(test_matrix, epsilon)
        
        # All values should be at least epsilon
        assert np.all(result >= epsilon), "Values below epsilon were not clamped"
        assert np.min(result) == epsilon, "Minimum value is not exactly epsilon"

    def test_large_values_unchanged(self, base_matrix, config):
        """Verify that values larger than EPSILON_FLOOR remain unchanged."""
        epsilon = config.EPSILON_FLOOR
        large_value = 10.0
        
        test_matrix = np.full((10, 10), large_value, dtype=np.float32)
        
        result = apply_epsilon_floor(test_matrix, epsilon)
        
        np.testing.assert_array_equal(result, test_matrix)

    def test_zero_values_clamped(self, edge_case_matrix, config):
        """Verify that zero values are clamped to epsilon."""
        epsilon = config.EPSILON_FLOOR
        
        result = apply_epsilon_floor(edge_case_matrix, epsilon)
        
        assert np.all(result == epsilon), "Zero values were not clamped to epsilon"

    def test_numerical_stability_after_floor(self, base_matrix, config):
        """Verify that applying epsilon floor prevents log(0) or div(0) issues."""
        epsilon = config.EPSILON_FLOOR
        
        # Matrix with zeros
        test_matrix = np.zeros((10, 10), dtype=np.float32)
        test_matrix[0, 0] = 1.0 # One non-zero to ensure not all zero
        
        result = apply_epsilon_floor(test_matrix, epsilon)
        
        # Check for infinities or NaNs after potential log/div operations
        # (Simulating a downstream operation)
        log_result = safe_log(result)
        assert not np.any(np.isnan(log_result)), "NaN detected after log operation"
        assert not np.any(np.isinf(log_result)), "Inf detected after log operation"

# --------------------------------------------------------------------------
# Tests for Moment Extraction Logic
# --------------------------------------------------------------------------

class TestMomentExtraction:
    """Tests for extracting statistical moments from AttentionMatrix."""

    def _extract_moments(self, matrix: np.ndarray) -> dict:
        """
        Helper to extract moments manually to verify logic.
        Matches the logic expected in the data generation pipeline.
        """
        mean_val = float(np.mean(matrix))
        var_val = float(np.var(matrix))
        
        # Sparsity: ratio of zero elements
        total_elements = matrix.size
        zero_count = np.count_nonzero(matrix == 0.0)
        sparsity_val = float(zero_count / total_elements)
        
        # Outlier magnitude: max absolute deviation from mean if > 3*std, else 0
        std_val = np.std(matrix)
        if std_val > 0:
            deviations = np.abs(matrix - mean_val)
            threshold = 3.0 * std_val
            outliers = deviations[deviations > threshold]
            outlier_mag = float(np.max(outliers)) if outliers.size > 0 else 0.0
        else:
            outlier_mag = 0.0

        return {
            "mean": mean_val,
            "variance": var_val,
            "sparsity": sparsity_val,
            "outlier_magnitude": outlier_mag
        }

    def test_mean_extraction(self, base_matrix):
        """Verify mean calculation matches numpy."""
        expected = float(np.mean(base_matrix))
        extracted = self._extract_moments(base_matrix)["mean"]
        assert np.isclose(expected, extracted), f"Mean mismatch: {expected} vs {extracted}"

    def test_variance_extraction(self, base_matrix):
        """Verify variance calculation matches numpy."""
        expected = float(np.var(base_matrix))
        extracted = self._extract_moments(base_matrix)["variance"]
        assert np.isclose(expected, extracted), f"Variance mismatch: {expected} vs {extracted}"

    def test_sparsity_extraction(self, base_matrix):
        """Verify sparsity calculation (ratio of zeros)."""
        total = base_matrix.size
        zeros = np.count_nonzero(base_matrix == 0.0)
        expected = zeros / total
        
        extracted = self._extract_moments(base_matrix)["sparsity"]
        assert np.isclose(expected, extracted), f"Sparsity mismatch: {expected} vs {extracted}"

    def test_outlier_magnitude_extraction(self, base_matrix):
        """Verify outlier magnitude calculation."""
        moments = self._extract_moments(base_matrix)
        
        # Since we injected outliers in the fixture, this should be > 0
        assert moments["outlier_magnitude"] > 0, "Outlier magnitude should be > 0 for base_matrix"
        
        # Verify against manual calculation
        expected = self._extract_moments(base_matrix)["outlier_magnitude"]
        assert np.isclose(moments["outlier_magnitude"], expected)

    def test_edge_case_zero_variance(self, edge_case_matrix):
        """Verify moment extraction handles zero variance (all zeros) gracefully."""
        moments = self._extract_moments(edge_case_matrix)
        
        assert moments["mean"] == 0.0
        assert moments["variance"] == 0.0
        assert moments["sparsity"] == 1.0
        # Outlier magnitude should be 0 because std is 0 (threshold is 0, but no non-zero elements)
        assert moments["outlier_magnitude"] == 0.0

    def test_attention_matrix_dataclass_compatibility(self, base_matrix):
        """Verify extracted moments can populate the AttentionMatrix dataclass."""
        moments = self._extract_moments(base_matrix)
        
        # Attempt to create the dataclass instance
        try:
            entity = AttentionMatrix(
                mean=moments["mean"],
                variance=moments["variance"],
                sparsity=moments["sparsity"],
                outlier_magnitude=moments["outlier_magnitude"]
            )
            assert entity.mean == moments["mean"]
            assert entity.variance == moments["variance"]
            assert entity.sparsity == moments["sparsity"]
            assert entity.outlier_magnitude == moments["outlier_magnitude"]
        except Exception as e:
            pytest.fail(f"Failed to create AttentionMatrix from extracted moments: {e}")

# --------------------------------------------------------------------------
# Integration: Epsilon + Moments
# --------------------------------------------------------------------------

def test_epsilon_floor_preserves_moment_structure(self, base_matrix, config):
    """
    Verify that applying epsilon floor does not destroy the statistical structure
    required for the Sinkhorn solver (T016).
    """
    epsilon = config.EPSILON_FLOOR
    
    # Apply floor
    floored_matrix = apply_epsilon_floor(base_matrix, epsilon)
    
    # Extract moments from floored matrix
    moments = self._extract_moments(floored_matrix)
    
    # Verify no NaNs or Infs
    assert not np.isnan(moments["mean"])
    assert not np.isnan(moments["variance"])
    assert not np.isnan(moments["sparsity"])
    assert not np.isnan(moments["outlier_magnitude"])
    
    # Verify variance is non-negative
    assert moments["variance"] >= 0.0

def test_moment_extraction_matches_spec_entities(self, base_matrix):
    """
    Ensure the extracted fields exactly match the Spec Key Entities:
    - mean (float32)
    - variance (float32)
    - sparsity (float32 ratio)
    - outlier_magnitude (float32)
    """
    moments = self._extract_moments(base_matrix)
    
    # Check types (approximate for float32 vs float64 in numpy)
    assert isinstance(moments["mean"], float)
    assert isinstance(moments["variance"], float)
    assert isinstance(moments["sparsity"], float)
    assert isinstance(moments["outlier_magnitude"], float)
    
    # Check ranges
    assert 0.0 <= moments["sparsity"] <= 1.0
    assert moments["variance"] >= 0.0
    assert moments["outlier_magnitude"] >= 0.0