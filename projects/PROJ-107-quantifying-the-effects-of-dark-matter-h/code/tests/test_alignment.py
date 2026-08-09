"""
Unit tests for angle calculation logic in alignment.py.

This module tests the mathematical correctness of dot product and arccos
based angle calculations used for halo-galaxy misalignment analysis.
"""
import pytest
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path
import sys

# Add project root to path for imports if running standalone
if 'code' not in sys.path:
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from utils.config import get_project_root


def calculate_angle_dot_arccos(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Calculate the angle (in degrees) between two vectors using dot product and arccos.

    This is the reference implementation for testing purposes, mirroring the logic
    expected in code/processing/alignment.py.

    Args:
        v1: First vector (numpy array)
        v2: Second vector (numpy array)

    Returns:
        Angle in degrees between 0 and 180.

    Raises:
        ValueError: If vectors are zero or dimensions mismatch.
    """
    v1 = np.array(v1, dtype=float)
    v2 = np.array(v2, dtype=float)

    if v1.shape != v2.shape:
        raise ValueError(f"Vector dimensions must match: {v1.shape} vs {v2.shape}")

    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)

    if norm1 < 1e-10 or norm2 < 1e-10:
        raise ValueError("Cannot calculate angle with zero-length vector")

    # Normalize
    v1_norm = v1 / norm1
    v2_norm = v2 / norm2

    # Dot product
    dot = np.dot(v1_norm, v2_norm)

    # Clamp to [-1, 1] to handle floating point errors
    dot = np.clip(dot, -1.0, 1.0)

    # Calculate angle in radians then convert to degrees
    angle_rad = np.arccos(dot)
    angle_deg = np.degrees(angle_rad)

    return float(angle_deg)


class TestAngleCalculation:
    """Unit tests for angle calculation (dot product/arccos)."""

    def test_identical_vectors_zero_angle(self):
        """Angle between identical vectors should be 0 degrees."""
        v1 = np.array([1.0, 2.0, 3.0])
        v2 = np.array([1.0, 2.0, 3.0])
        angle = calculate_angle_dot_arccos(v1, v2)
        assert np.isclose(angle, 0.0, atol=1e-6)

    def test_orthogonal_vectors_ninety_angle(self):
        """Angle between orthogonal vectors should be 90 degrees."""
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([0.0, 1.0, 0.0])
        angle = calculate_angle_dot_arccos(v1, v2)
        assert np.isclose(angle, 90.0, atol=1e-6)

    def test_opposite_vectors_one_eighty_angle(self):
        """Angle between opposite vectors should be 180 degrees."""
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([-1.0, 0.0, 0.0])
        angle = calculate_angle_dot_arccos(v1, v2)
        assert np.isclose(angle, 180.0, atol=1e-6)

    def test_general_vectors_45_degrees(self):
        """Test with vectors known to form 45 degree angle."""
        # v1 = (1, 0), v2 = (1, 1) -> angle is 45 degrees
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([1.0, 1.0, 0.0])
        angle = calculate_angle_dot_arccos(v1, v2)
        assert np.isclose(angle, 45.0, atol=1e-6)

    def test_general_vectors_60_degrees(self):
        """Test with vectors known to form 60 degree angle."""
        # v1 = (1, 0, 0), v2 = (0.5, sqrt(3)/2, 0) -> angle is 60 degrees
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([0.5, np.sqrt(3)/2, 0.0])
        angle = calculate_angle_dot_arccos(v1, v2)
        assert np.isclose(angle, 60.0, atol=1e-6)

    def test_scalar_multiplication_invariance(self):
        """Angle should be invariant to scalar multiplication of vectors."""
        v1 = np.array([1.0, 2.0, 3.0])
        v2 = np.array([4.0, 5.0, 6.0])
        angle_original = calculate_angle_dot_arccos(v1, v2)

        v1_scaled = v1 * 10.5
        v2_scaled = v2 * -2.3
        angle_scaled = calculate_angle_dot_arccos(v1_scaled, v2_scaled)

        # Note: Scaling by negative flips direction, so angle might be 180 - original
        # Let's check with positive scaling
        v1_scaled_pos = v1 * 2.0
        v2_scaled_pos = v2 * 3.0
        angle_scaled_pos = calculate_angle_dot_arccos(v1_scaled_pos, v2_scaled_pos)

        assert np.isclose(angle_original, angle_scaled_pos, atol=1e-6)

    def test_dimension_mismatch_raises_error(self):
        """Different dimension vectors should raise ValueError."""
        v1 = np.array([1.0, 2.0, 3.0])
        v2 = np.array([1.0, 2.0])
        with pytest.raises(ValueError):
            calculate_angle_dot_arccos(v1, v2)

    def test_zero_vector_raises_error(self):
        """Zero vector should raise ValueError."""
        v1 = np.array([0.0, 0.0, 0.0])
        v2 = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            calculate_angle_dot_arccos(v1, v2)

    def test_clamping_handles_floating_point_errors(self):
        """Clamping should prevent NaN from slight floating point errors."""
        # Create a case where dot product might slightly exceed 1.0 due to precision
        v1 = np.array([1.0, 0.0, 0.0])
        v2 = np.array([1.0 + 1e-15, 1e-15, 0.0])
        # This should not raise or return NaN
        angle = calculate_angle_dot_arccos(v1, v2)
        assert not np.isnan(angle)
        assert 0.0 <= angle <= 180.0

    def test_3d_vectors(self):
        """Test with general 3D vectors."""
        v1 = np.array([1.0, 2.0, 3.0])
        v2 = np.array([4.0, 5.0, 6.0])
        angle = calculate_angle_dot_arccos(v1, v2)
        # Verify against numpy's built-in function
        expected = np.degrees(np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))))
        assert np.isclose(angle, expected, atol=1e-6)

    def test_random_vectors_consistency(self):
        """Test consistency with multiple random vector pairs."""
        np.random.seed(42)  # For reproducibility
        for _ in range(10):
            v1 = np.random.randn(3)
            v2 = np.random.randn(3)
            angle = calculate_angle_dot_arccos(v1, v2)
            # Verify against numpy
            expected = np.degrees(np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))))
            assert np.isclose(angle, expected, atol=1e-6)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])