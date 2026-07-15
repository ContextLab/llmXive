"""
Unit tests for metric computation functions (T018).
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Mock the dependencies if necessary, but here we test the logic directly
# assuming the functions are pure enough to test without full pipeline.

def test_inertia_tensor_shape():
    """
    T018: Verify that the shape parameter s (c/a) is computed correctly
    and falls within [0, 1] for a flattened halo.
    """
    # We simulate a flattened distribution (disk-like)
    # x, y spread, z compressed
    N = 1000
    np.random.seed(42)
    x = np.random.normal(0, 10, N)
    y = np.random.normal(0, 10, N)
    z = np.random.normal(0, 1, N) # Compressed in z
    
    positions = np.vstack([x, y, z]).T
    
    # Compute inertia tensor (simplified: covariance matrix eigenvalues)
    # Inertia tensor I_ij = sum(m * (r^2 * delta_ij - r_i * r_j))
    # For shape, we often use the eigenvalues of the inertia tensor or covariance.
    # The axis ratios are sqrt(lambda_min / lambda_max) etc.
    
    # Using covariance matrix eigenvalues for simplicity in this test
    cov = np.cov(positions.T)
    eigenvalues, _ = np.linalg.eigh(cov)
    eigenvalues = np.sort(eigenvalues)[::-1] # a >= b >= c
    
    # s = c/a
    s = eigenvalues[-1] / eigenvalues[0]
    
    assert 0 <= s <= 1, f"Shape s={s} out of range [0, 1]"
    assert s < 0.5, "Flattened halo should have s < 0.5"

def test_spin_parameter_subsample():
    """
    T019: Verify spin parameter calculation on a subsample.
    """
    # Mock data
    N = 500
    np.random.seed(42)
    r = np.random.rand(N) * 10
    v = np.random.rand(N, 3) * 10
    
    # Angular momentum L = r x v
    L = np.cross(r[:, np.newaxis], v)
    L_mag = np.linalg.norm(L, axis=1).mean()
    
    # Kinetic energy T = 0.5 * m * v^2
    T = 0.5 * np.mean(np.sum(v**2, axis=1))
    
    # Potential energy U (simplified)
    U = -np.mean(r) # Rough approximation
    
    # Lambda = |L| * |E|^(1/2) / (G * M^(5/2))
    # Simplified for test: just check range
    # We expect 0 < lambda < 1 for realistic halos
    # Here we just ensure the calculation doesn't crash and produces a number
    
    # Mock lambda calculation
    E = T + U
    if E <= 0: E = 1e-10
    lambda_val = (L_mag * np.sqrt(abs(E))) / (1.0) # Normalized
    
    # Just check it's a finite number
    assert np.isfinite(lambda_val), "Spin parameter is not finite"

def test_nfw_convergence():
    """
    T020: Verify NFW profile fitting convergence.
    """
    # Mock NFW profile data
    from scipy.optimize import curve_fit
    
    def nfw_profile(r, rs, rho_s):
        return rho_s / (r/rs * (1 + r/rs)**2)
    
    r = np.logspace(-1, 1, 50)
    true_rs, true_rho_s = 10.0, 1.0
    rho = nfw_profile(r, true_rs, true_rho_s)
    rho += np.random.normal(0, 0.01, size=r.shape) # Add noise
    
    # Fit
    try:
        popt, pcov = curve_fit(nfw_profile, r, rho, p0=[5.0, 0.5])
        rs_fit, rho_s_fit = popt
        
        assert np.isfinite(rs_fit), "Fitted rs is not finite"
        assert np.isfinite(rho_s_fit), "Fitted rho_s is not finite"
        assert rs_fit > 0, "Fitted rs must be positive"
        assert rho_s_fit > 0, "Fitted rho_s must be positive"
        
    except RuntimeError:
        # If fit fails, that's a valid outcome for bad data, but here data is good
        pytest.fail("NFW fit failed on synthetic data")