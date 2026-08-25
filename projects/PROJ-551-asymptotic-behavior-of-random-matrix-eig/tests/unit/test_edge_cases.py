"""
Unit tests for edge cases in random matrix eigenvalue analysis.
Covers: N=100, theta=1.0, rank=0 scenarios.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from analysis.eigen_solver import compute_top_eigenvalues, validate_eigenvalues
from analysis.outlier_detect import detect_outliers, calculate_bbp_threshold
from utils.config import get_tolerance


class TestEdgeCaseSmallN:
    """Tests for small matrix size (N=100)."""

    def test_wigner_generation_small_n(self):
        """Verify Wigner matrix generation for N=100."""
        N = 100
        seed = 42
        matrix = generate_wigner_matrix(N, seed=seed)

        assert matrix.shape == (N, N), f"Expected shape ({N}, {N}), got {matrix.shape}"
        assert np.allclose(matrix, matrix.T, atol=1e-10), "Matrix must be symmetric"

        # Check scaling: entries should be O(1/sqrt(N))
        # For Wigner, off-diagonal variance is 1/N, diagonal is 2/N (usually)
        off_diag = matrix[np.triu_indices(N, k=1)]
        expected_var = 1.0 / N
        actual_var = np.var(off_diag)
        # Allow some tolerance due to randomness
        assert 0.5 * expected_var < actual_var < 1.5 * expected_var, \
            f"Variance {actual_var} not close to expected {expected_var}"

    def test_eigenvalue_computation_small_n(self):
        """Verify eigenvalue computation for N=100."""
        N = 100
        seed = 42
        matrix = generate_wigner_matrix(N, seed=seed)

        # Compute top 10 eigenvalues
        eigenvalues = compute_top_eigenvalues(matrix, k=10)

        assert len(eigenvalues) == 10, f"Expected 10 eigenvalues, got {len(eigenvalues)}"
        assert all(isinstance(ev, (float, np.floating)) for ev in eigenvalues), \
            "All eigenvalues must be numeric"

        # For Wigner matrix, eigenvalues should be in [-2, 2] approximately
        # Allow some margin for finite N
        max_ev = max(eigenvalues)
        min_ev = min(eigenvalues)
        assert max_ev < 2.5, f"Max eigenvalue {max_ev} exceeds expected bound"
        assert min_ev > -2.5, f"Min eigenvalue {min_ev} below expected bound"

    def test_no_outlier_small_n_no_perturbation(self):
        """Verify no outliers detected for unperturbed N=100 matrix."""
        N = 100
        seed = 42
        matrix = generate_wigner_matrix(N, seed=seed)

        eigenvalues = compute_top_eigenvalues(matrix, k=10)
        bbp_edge = 2.0  # Theoretical edge for unperturbed Wigner

        outliers = detect_outliers(eigenvalues, perturbation_norm=0.0)

        # Without perturbation, no eigenvalues should be flagged as outliers
        # (or at most numerical noise near edge)
        assert len(outliers) == 0, f"Expected 0 outliers, got {len(outliers)}"


class TestEdgeCaseCriticalTheta:
    """Tests for theta=1.0 (at the BBP transition threshold)."""

    def test_bbp_threshold_calculation(self):
        """Verify BBP threshold calculation for theta=1.0."""
        # For theta <= 1, no outlier should emerge
        theta = 1.0
        bbp_threshold = calculate_bbp_threshold(theta)

        assert bbp_threshold == 2.0, \
            f"Expected BBP threshold 2.0 for theta=1.0, got {bbp_threshold}"

    def test_no_outlier_at_critical_theta(self):
        """Verify no outlier at exactly theta=1.0."""
        N = 1000  # Use larger N for clearer asymptotic behavior
        seed = 42
        matrix = generate_wigner_matrix(N, seed=seed)

        # Create perturbation with theta=1.0 (at threshold)
        perturbation = create_perturbation(N, rank=1, theta=1.0, density=1.0)

        perturbed_matrix = matrix + perturbation

        eigenvalues = compute_top_eigenvalues(perturbed_matrix, k=10)

        # At theta=1.0, the outlier should merge with the bulk
        # Allow small numerical tolerance
        max_ev = max(eigenvalues)
        assert max_ev <= 2.0 + 1e-2, \
            f"Max eigenvalue {max_ev} should be at bulk edge for theta=1.0"

    def test_outlier_above_critical_theta(self):
        """Verify outlier emerges for theta > 1.0."""
        N = 1000
        seed = 42
        matrix = generate_wigner_matrix(N, seed=seed)

        theta = 1.5  # Above threshold
        perturbation = create_perturbation(N, rank=1, theta=theta, density=1.0)

        perturbed_matrix = matrix + perturbation

        eigenvalues = compute_top_eigenvalues(perturbed_matrix, k=10)

        # BBP prediction: lambda_out = theta + 1/theta
        expected_outlier = theta + 1.0 / theta

        max_ev = max(eigenvalues)
        # Check that max eigenvalue is significantly above 2.0
        assert max_ev > 2.0 + 1e-2, \
            f"Max eigenvalue {max_ev} should exceed bulk edge for theta={theta}"
        # Check proximity to BBP prediction (allow some finite-N error)
        assert abs(max_ev - expected_outlier) < 0.3, \
            f"Max eigenvalue {max_ev} not close to BBP prediction {expected_outlier}"


class TestEdgeCaseRankZero:
    """Tests for rank-0 perturbation (unperturbed Wigner matrix)."""

    def test_rank_zero_perturbation_is_zero(self):
        """Verify rank-0 perturbation is zero matrix."""
        N = 100
        perturbation = create_perturbation(N, rank=0, theta=2.5, density=1.0)

        assert np.allclose(perturbation, 0), \
            "Rank-0 perturbation should be zero matrix"

    def test_no_outlier_rank_zero(self):
        """Verify no outliers for rank-0 perturbation."""
        N = 1000
        seed = 42
        matrix = generate_wigner_matrix(N, seed=seed)

        perturbation = create_perturbation(N, rank=0, theta=2.5, density=1.0)
        perturbed_matrix = matrix + perturbation

        eigenvalues = compute_top_eigenvalues(perturbed_matrix, k=10)

        outliers = detect_outliers(eigenvalues, perturbation_norm=0.0)

        assert len(outliers) == 0, \
            f"Expected 0 outliers for rank-0 perturbation, got {len(outliers)}"

    def test_semicircle_law_compliance_rank_zero(self):
        """Verify eigenvalue distribution follows semicircle law for rank-0."""
        N = 5000  # Large N for better approximation
        seed = 42
        matrix = generate_wigner_matrix(N, seed=seed)

        # Compute all eigenvalues (not just top 10)
        all_eigenvalues = np.linalg.eigvalsh(matrix)

        # Check that max eigenvalue is close to 2.0
        max_ev = max(all_eigenvalues)
        min_ev = min(all_eigenvalues)

        # For large N, should be close to [-2, 2]
        assert max_ev < 2.1, f"Max eigenvalue {max_ev} exceeds semicircle edge"
        assert min_ev > -2.1, f"Min eigenvalue {min_ev} below semicircle edge"

        # Check mean and variance
        mean_ev = np.mean(all_eigenvalues)
        assert abs(mean_ev) < 0.1, f"Mean eigenvalue {mean_ev} should be near 0"


class TestEdgeCaseNumericalStability:
    """Tests for numerical stability at edge cases."""

    def test_tolerance_validation(self):
        """Verify eigenvalue validation respects tolerance."""
        N = 100
        seed = 42
        matrix = generate_wigner_matrix(N, seed=seed)

        eigenvalues = compute_top_eigenvalues(matrix, k=10)

        # Validate with default tolerance
        is_valid, details = validate_eigenvalues(eigenvalues, tol=get_tolerance())

        assert is_valid, "Eigenvalue computation should be valid within tolerance"
        assert "converged" in details or "valid" in details, \
            f"Validation details missing: {details}"

    def test_symmetry_preservation_small_n(self):
        """Verify symmetry is preserved for small N."""
        for N in [10, 50, 100]:
            seed = 42
            matrix = generate_wigner_matrix(N, seed=seed)

            # Check symmetry with tight tolerance
            assert np.allclose(matrix, matrix.T, atol=1e-10), \
                f"Matrix of size {N} is not symmetric"

    def test_eigenvalue_realness(self):
        """Verify all eigenvalues are real for symmetric matrices."""
        N = 100
        seed = 42
        matrix = generate_wigner_matrix(N, seed=seed)

        eigenvalues = compute_top_eigenvalues(matrix, k=10)

        for ev in eigenvalues:
            assert isinstance(ev, (float, np.floating)), \
                f"Eigenvalue {ev} is not real"

class TestEdgeCaseIntegration:
    """Integration tests combining multiple edge cases."""

    def test_full_pipeline_small_n_critical_theta(self):
        """Run full pipeline for N=100, theta=1.0."""
        N = 100
        seed = 42
        theta = 1.0

        matrix = generate_wigner_matrix(N, seed=seed)
        perturbation = create_perturbation(N, rank=1, theta=theta, density=1.0)
        perturbed_matrix = matrix + perturbation

        eigenvalues = compute_top_eigenvalues(perturbed_matrix, k=10)
        outliers = detect_outliers(eigenvalues, perturbation_norm=theta)

        # At critical theta, should have 0 or very few outliers
        assert len(outliers) <= 1, \
            f"Expected at most 1 outlier at critical theta, got {len(outliers)}"

    def test_full_pipeline_rank_zero_large_n(self):
        """Run full pipeline for large N, rank=0."""
        N = 2000
        seed = 42

        matrix = generate_wigner_matrix(N, seed=seed)
        perturbation = create_perturbation(N, rank=0, theta=2.5, density=1.0)
        perturbed_matrix = matrix + perturbation

        eigenvalues = compute_top_eigenvalues(perturbed_matrix, k=10)
        outliers = detect_outliers(eigenvalues, perturbation_norm=0.0)

        assert len(outliers) == 0, \
            f"Expected 0 outliers for rank-0, got {len(outliers)}"
        assert max(eigenvalues) < 2.1, \
            f"Max eigenvalue {max(eigenvalues)} should be within semicircle"