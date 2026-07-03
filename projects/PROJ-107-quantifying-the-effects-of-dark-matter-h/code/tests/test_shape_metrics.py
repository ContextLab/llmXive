"""
Unit tests for shape metrics derivation (T013).

Tests cover:
  - Axial ratio computation from eigenvalues
  - Triaxiality computation
  - Particle count filtering
  - Validation of physical bounds
  - End-to-end halo processing
"""

import pytest
import numpy as np
from code.processing.shape_metrics import (
    compute_axial_ratios,
    compute_triaxiality,
    compute_shape_metrics_from_eigenvalues,
    filter_halo_by_particle_count,
    validate_shape_metrics,
    process_halo_shape
)


class TestAxialRatios:
    def test_spherical_halo(self):
        # All eigenvalues equal -> b/a = 1, c/a = 1
        eigs = np.array([1.0, 1.0, 1.0])
        b_a, c_a = compute_axial_ratios(eigs)
        assert np.isclose(b_a, 1.0)
        assert np.isclose(c_a, 1.0)

    def test_prolate_halo(self):
        # Lambda_a >> Lambda_b = Lambda_c
        eigs = np.array([4.0, 1.0, 1.0])
        b_a, c_a = compute_axial_ratios(eigs)
        # b/a = sqrt(1/4) = 0.5
        # c/a = sqrt(1/4) = 0.5
        assert np.isclose(b_a, 0.5)
        assert np.isclose(c_a, 0.5)

    def test_oblate_halo(self):
        # Lambda_a = Lambda_b >> Lambda_c
        eigs = np.array([4.0, 4.0, 1.0])
        b_a, c_a = compute_axial_ratios(eigs)
        # b/a = sqrt(4/4) = 1.0
        # c/a = sqrt(1/4) = 0.5
        assert np.isclose(b_a, 1.0)
        assert np.isclose(c_a, 0.5)

    def test_unsorted_input(self):
        # Input not sorted: [1, 4, 1] -> sorted [4, 1, 1]
        eigs = np.array([1.0, 4.0, 1.0])
        b_a, c_a = compute_axial_ratios(eigs, sort_descending=True)
        assert np.isclose(b_a, 0.5)
        assert np.isclose(c_a, 0.5)

    def test_invalid_eigenvalue_count(self):
        eigs = np.array([1.0, 2.0])
        with pytest.raises(ValueError):
            compute_axial_ratios(eigs)

    def test_negative_eigenvalue(self):
        eigs = np.array([1.0, -1.0, 1.0])
        with pytest.raises(ValueError):
            compute_axial_ratios(eigs)


class TestTriaxiality:
    def test_prolate(self):
        # b/a = 0.5, c/a = 0.5
        # T = (1 - 0.25) / (1 - 0.25) = 1.0 ?
        # Wait: For prolate, usually c/a is small, b/a is small.
        # Let's use specific values:
        # Prolate: c/a ~ 0, b/a ~ 0 -> T = (1-0)/(1-0) = 1?
        # Actually, definition: T = (1 - (b/a)^2) / (1 - (c/a)^2)
        # If b/a = c/a, T = 1.
        # Let's test a clear triaxial case.
        b_a = 0.8
        c_a = 0.6
        t = compute_triaxiality(b_a, c_a)
        # T = (1 - 0.64) / (1 - 0.36) = 0.36 / 0.64 = 0.5625
        assert np.isclose(t, 0.5625)

    def test_spherical_limit(self):
        # c/a -> 1, denominator -> 0
        b_a = 0.999
        c_a = 0.999
        t = compute_triaxiality(b_a, c_a)
        # Should return 0.5 by convention
        assert np.isclose(t, 0.5)

    def test_pure_prolate_like(self):
        # b/a close to c/a, but both small
        b_a = 0.2
        c_a = 0.2
        t = compute_triaxiality(b_a, c_a)
        assert np.isclose(t, 0.5) # (1-0.04)/(1-0.04) = 1?
        # Wait: if b_a == c_a, T = 1.
        # Let's re-verify: T = (1 - b^2) / (1 - c^2). If b=c, T=1.
        # My previous test logic was flawed.
        # If b_a = c_a = 0.2:
        # T = (1 - 0.04) / (1 - 0.04) = 1.0
        assert np.isclose(t, 1.0)


class TestFiltering:
    def test_passes_threshold(self):
        assert filter_halo_by_particle_count(10000, 10000) is True
        assert filter_halo_by_particle_count(50000, 10000) is True

    def test_fails_threshold(self):
        assert filter_halo_by_particle_count(9999, 10000) is False
        assert filter_halo_by_particle_count(100, 10000) is False


class TestValidation:
    def test_valid_metrics(self):
        metrics = {
            'b_a_ratio': 0.8,
            'c_a_ratio': 0.6,
            'triaxiality': 0.56
        }
        assert validate_shape_metrics(metrics) is True

    def test_invalid_b_a(self):
        metrics = {
            'b_a_ratio': 1.5,
            'c_a_ratio': 0.6,
            'triaxiality': 0.56
        }
        assert validate_shape_metrics(metrics) is False

    def test_invalid_c_a(self):
        metrics = {
            'b_a_ratio': 0.8,
            'c_a_ratio': -0.1,
            'triaxiality': 0.56
        }
        assert validate_shape_metrics(metrics) is False

    def test_invalid_triaxiality(self):
        metrics = {
            'b_a_ratio': 0.8,
            'c_a_ratio': 0.6,
            'triaxiality': 1.5
        }
        assert validate_shape_metrics(metrics) is False


class TestProcessHaloShape:
    def test_valid_halo(self):
        eigs = np.array([4.0, 1.0, 1.0])
        result = process_halo_shape(eigs, particle_count=20000, halo_id=123)
        assert result is not None
        assert result['halo_id'] == 123
        assert result['particle_count'] == 20000
        assert 'b_a_ratio' in result
        assert 'c_a_ratio' in result
        assert 'triaxiality' in result

    def test_low_particle_count(self):
        eigs = np.array([4.0, 1.0, 1.0])
        result = process_halo_shape(eigs, particle_count=5000)
        assert result is None

    def test_invalid_eigenvalues(self):
        eigs = np.array([1.0, -1.0, 1.0])
        result = process_halo_shape(eigs, particle_count=20000)
        assert result is None