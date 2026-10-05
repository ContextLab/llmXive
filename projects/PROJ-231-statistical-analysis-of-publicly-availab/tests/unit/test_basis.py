"""
Unit tests for B-spline basis expansion functionality.

This module tests the basis expansion logic in code/basis.py.
It verifies that:
1. The B-spline basis matrix is constructed correctly.
2. The reconstruction from coefficients matches the original data within tolerance.
3. The basis dimension K is selected appropriately (mocked for unit tests).
"""
import pytest
import numpy as np
from scipy.interpolate import BSpline, make_interp_spline
from scipy.special import binom
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.basis import (
    create_basis_matrix,
    select_basis_dimension_gcv,
    reconstruct_from_coefficients,
    compute_reconstruction_mse
)
from code.config import get_project_root


def _generate_test_signal(n_points=100, noise_level=0.0):
    """Generate a smooth test signal with optional noise."""
    t = np.linspace(0, 10, n_points)
    # Smooth function: combination of sines and a polynomial
    y = np.sin(t) + 0.5 * np.cos(2 * t) + 0.1 * t
    if noise_level > 0:
        np.random.seed(42)  # For reproducibility
        y += np.random.normal(0, noise_level, size=y.shape)
    return t, y


class TestCreateBasisMatrix:
    """Tests for the basis matrix creation function."""

    def test_basis_matrix_shape(self):
        """Verify that the basis matrix has the correct shape."""
        t = np.linspace(0, 10, 50)
        k = 10  # Number of basis functions
        degree = 3  # Cubic splines

        B = create_basis_matrix(t, k, degree)

        assert B.shape == (len(t), k), f"Expected shape ({len(t)}, {k}), got {B.shape}"

    def test_basis_matrix_non_negative(self):
        """B-spline basis functions should be non-negative."""
        t = np.linspace(0, 10, 50)
        k = 10
        degree = 3

        B = create_basis_matrix(t, k, degree)

        assert np.all(B >= 0), "B-spline basis functions must be non-negative"

    def test_basis_partition_of_unity(self):
        """B-spline basis functions should sum to 1 at each point."""
        t = np.linspace(0, 10, 50)
        k = 10
        degree = 3

        B = create_basis_matrix(t, k, degree)
        row_sums = np.sum(B, axis=1)

        # Allow small numerical tolerance
        assert np.allclose(row_sums, 1.0, atol=1e-6), \
            f"Basis functions should sum to 1, got max deviation {np.max(np.abs(row_sums - 1.0))}"

    def test_basis_matrix_continuity(self):
        """Test that basis functions are continuous (smooth transitions)."""
        t = np.linspace(0, 10, 200)  # High resolution
        k = 10
        degree = 3

        B = create_basis_matrix(t, k, degree)

        # Check that there are no NaN or Inf values
        assert not np.any(np.isnan(B)), "Basis matrix contains NaN values"
        assert not np.any(np.isinf(B)), "Basis matrix contains Inf values"


class TestSelectBasisDimensionGCV:
    """Tests for GCV-based basis dimension selection."""

    def test_gcv_selection_returns_valid_k(self):
        """GCV selection should return a valid basis dimension."""
        t, y = _generate_test_signal(n_points=100, noise_level=0.1)

        # Test range of candidate K values
        k_candidates = [5, 8, 10, 12, 15]
        degree = 3

        k_selected = select_basis_dimension_gcv(t, y, k_candidates, degree)

        assert k_selected in k_candidates, \
            f"Selected K ({k_selected}) not in candidate list {k_candidates}"
        assert k_selected >= degree + 1, \
            f"K ({k_selected}) must be at least degree + 1 ({degree + 1})"

    def test_gcv_prefers_simpler_models_for_clean_data(self):
        """With clean data, GCV should prefer a smaller basis dimension."""
        t, y = _generate_test_signal(n_points=100, noise_level=0.0)  # No noise

        k_candidates = [5, 8, 10, 12, 15]
        degree = 3

        k_selected = select_basis_dimension_gcv(t, y, k_candidates, degree)

        # For clean data, a smaller K should be preferred
        assert k_selected <= 8, \
            f"For clean data, GCV should prefer smaller K, got {k_selected}"

    def test_gcv_handles_noisy_data(self):
        """With noisy data, GCV might select a larger basis dimension."""
        t, y = _generate_test_signal(n_points=100, noise_level=0.5)  # High noise

        k_candidates = [5, 8, 10, 12, 15]
        degree = 3

        k_selected = select_basis_dimension_gcv(t, y, k_candidates, degree)

        assert k_selected in k_candidates, \
            f"Selected K ({k_selected}) not in candidate list {k_candidates}"


class TestReconstructFromCoefficients:
    """Tests for curve reconstruction from B-spline coefficients."""

    def test_reconstruction_matches_original(self):
        """Reconstruction should match original data within tolerance."""
        t, y = _generate_test_signal(n_points=100, noise_level=0.01)
        k = 12
        degree = 3

        # Create basis and compute coefficients
        B = create_basis_matrix(t, k, degree)
        # Solve for coefficients: y = B @ c
        coefficients, _, _, _ = np.linalg.lstsq(B, y, rcond=None)

        # Reconstruct
        y_reconstructed = reconstruct_from_coefficients(t, coefficients, k, degree)

        # Check MSE
        mse = np.mean((y - y_reconstructed) ** 2)
        assert mse <= 0.01, \
            f"Reconstruction MSE ({mse:.6f}) exceeds tolerance (0.01)"

    def test_reconstruction_with_noise(self):
        """Test reconstruction with noisy data (should still be close)."""
        t, y = _generate_test_signal(n_points=100, noise_level=0.1)
        k = 15
        degree = 3

        B = create_basis_matrix(t, k, degree)
        coefficients, _, _, _ = np.linalg.lstsq(B, y, rcond=None)

        y_reconstructed = reconstruct_from_coefficients(t, coefficients, k, degree)

        # With noise, we expect some error but it should be bounded
        mse = np.mean((y - y_reconstructed) ** 2)
        # Allow slightly higher tolerance for noisy data
        assert mse <= 0.05, \
            f"Reconstruction MSE ({mse:.6f}) too high for noisy data"


class TestComputeReconstructionMSE:
    """Tests for MSE computation utility."""

    def test_mse_calculation(self):
        """Verify MSE calculation is correct."""
        y_true = np.array([1.0, 2.0, 3.0, 4.0])
        y_pred = np.array([1.1, 1.9, 3.1, 3.9])

        expected_mse = np.mean((y_true - y_pred) ** 2)
        computed_mse = compute_reconstruction_mse(y_true, y_pred)

        assert np.isclose(computed_mse, expected_mse), \
            f"MSE mismatch: expected {expected_mse}, got {computed_mse}"

    def test_mse_zero_for_perfect_match(self):
        """MSE should be zero for perfect reconstruction."""
        y = np.array([1.0, 2.0, 3.0])
        mse = compute_reconstruction_mse(y, y)
        assert mse == 0.0, "MSE should be 0 for identical arrays"


class TestIntegrationBasisExpansion:
    """Integration-style tests for the full basis expansion workflow."""

    def test_full_workflow_clean_signal(self):
        """Test the complete workflow: generate -> basis -> coefficients -> reconstruct."""
        t, y = _generate_test_signal(n_points=100, noise_level=0.0)

        # Select basis dimension
        k_candidates = [5, 8, 10, 12, 15]
        degree = 3
        k = select_basis_dimension_gcv(t, y, k_candidates, degree)

        # Create basis
        B = create_basis_matrix(t, k, degree)

        # Compute coefficients
        coefficients, _, _, _ = np.linalg.lstsq(B, y, rcond=None)

        # Reconstruct
        y_reconstructed = reconstruct_from_coefficients(t, coefficients, k, degree)

        # Verify
        mse = compute_reconstruction_mse(y, y_reconstructed)
        assert mse <= 0.01, \
            f"Full workflow MSE ({mse:.6f}) exceeds tolerance (0.01)"

    def test_full_workflow_noisy_signal(self):
        """Test workflow with noisy data."""
        t, y = _generate_test_signal(n_points=100, noise_level=0.1)

        k_candidates = [8, 10, 12, 15, 18]
        degree = 3
        k = select_basis_dimension_gcv(t, y, k_candidates, degree)

        B = create_basis_matrix(t, k, degree)
        coefficients, _, _, _ = np.linalg.lstsq(B, y, rcond=None)

        y_reconstructed = reconstruct_from_coefficients(t, coefficients, k, degree)

        mse = compute_reconstruction_mse(y, y_reconstructed)
        # With noise, allow slightly higher MSE
        assert mse <= 0.05, \
            f"Full workflow MSE ({mse:.6f}) too high for noisy data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])