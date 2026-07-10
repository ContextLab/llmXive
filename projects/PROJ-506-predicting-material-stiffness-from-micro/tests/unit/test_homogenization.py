"""
Unit tests for FFT-based homogenization solver.
"""
import numpy as np
import pytest
from code.utils.fft_homogenization import compute_effective_stiffness


def test_homogeneous_material():
    """
    Test that a fully homogeneous material returns the theoretical stiffness tensor.
    """
    N = 64
    E0 = 210.0e9
    nu0 = 0.3
    microstructure = np.ones((N, N))

    C_eff = compute_effective_stiffness(
        microstructure,
        E0=E0,
        nu0=nu0,
        n_iterations=20,
        tolerance=1e-4
    )

    # Theoretical values for plane strain
    mu = E0 / (2.0 * (1.0 + nu0))
    lam = (E0 * nu0) / ((1.0 + nu0) * (1.0 - 2.0 * nu0))

    C11_theory = lam + 2 * mu
    C12_theory = lam
    C66_theory = mu

    # Check diagonal elements (allowing for small numerical error)
    assert np.isclose(C_eff[0, 0], C11_theory, rtol=1e-2), f"C11 mismatch: {C_eff[0,0]} vs {C11_theory}"
    assert np.isclose(C_eff[1, 1], C11_theory, rtol=1e-2), f"C22 mismatch: {C_eff[1,1]} vs {C11_theory}"
    assert np.isclose(C_eff[0, 1], C12_theory, rtol=1e-2), f"C12 mismatch: {C_eff[0,1]} vs {C12_theory}"
    assert np.isclose(C_eff[2, 2], C66_theory, rtol=1e-2), f"C66 mismatch: {C_eff[2,2]} vs {C66_theory}"


def test_void_material():
    """
    Test that a fully void material returns near-zero stiffness.
    """
    N = 64
    microstructure = np.zeros((N, N))

    C_eff = compute_effective_stiffness(
        microstructure,
        E0=210.0e9,
        nu0=0.3,
        n_iterations=20
    )

    # Should be very close to zero (due to epsilon regularization)
    assert np.allclose(C_eff, 0.0, atol=1e-6), "Void material should have near-zero stiffness"


def test_convergence():
    """
    Test that the solver converges for a simple checkerboard pattern.
    """
    N = 32
    microstructure = np.zeros((N, N))
    microstructure[::2, ::2] = 1.0
    microstructure[1::2, 1::2] = 1.0

    # Run with a small number of iterations to ensure it doesn't crash
    # and produces a finite result
    C_eff = compute_effective_stiffness(
        microstructure,
        E0=1.0,
        nu0=0.3,
        n_iterations=50,
        tolerance=1e-5
    )

    assert np.all(np.isfinite(C_eff)), "Stiffness tensor should be finite"
    # Stiffness should be between 0 and 1 (normalized)
    assert np.all(C_eff >= 0), "Stiffness should be non-negative"
    assert np.all(C_eff <= 2.0), "Stiffness should not exceed theoretical max significantly"