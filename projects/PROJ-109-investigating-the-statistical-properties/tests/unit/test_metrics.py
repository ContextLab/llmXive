"""
Unit tests for metric computation functions (T018).
Tests the inertia tensor shape calculation and related metrics.
"""
import pytest
import numpy as np
from pathlib import Path
import sys

# Ensure code directory is in path for imports if running standalone
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from data.compute_metrics import compute_halo_metrics


def test_inertia_tensor_shape():
    """
    T018: Verify that the shape parameter s (c/a) is computed correctly
    and falls within [0, 1] for a flattened halo.
    
    This test constructs a synthetic halo with a known flattened geometry
    (disk-like) and verifies that the computed shape parameter 's' reflects
    this flattening (s < 0.5) and remains within physical bounds [0, 1].
    """
    # Simulate a flattened distribution (disk-like)
    # x, y spread, z compressed
    N = 1000
    np.random.seed(42)
    x = np.random.normal(0, 10, N)
    y = np.random.normal(0, 10, N)
    z = np.random.normal(0, 1, N)  # Compressed in z
    
    positions = np.vstack([x, y, z]).T
    masses = np.ones(N)  # Uniform mass for simplicity
    
    # Call the actual implementation
    # compute_halo_metrics expects a dict with 'particle_positions' and 'particle_masses'
    halo_data = {
        'particle_positions': positions,
        'particle_masses': masses
    }
    
    results = compute_halo_metrics(halo_data)
    
    s = results['shape']
    
    # Assertions
    assert 0 <= s <= 1, f"Shape s={s} out of range [0, 1]"
    assert s < 0.5, f"Flattened halo should have s < 0.5, but got {s}"
    assert np.isfinite(s), "Shape parameter must be finite"


def test_inertia_tensor_spherical():
    """
    Verify that a spherical distribution yields s ≈ 1.
    """
    N = 1000
    np.random.seed(123)
    # Spherical distribution
    r = np.random.normal(0, 10, (N, 3))
    positions = r
    masses = np.ones(N)
    
    halo_data = {
        'particle_positions': positions,
        'particle_masses': masses
    }
    
    results = compute_halo_metrics(halo_data)
    s = results['shape']
    
    # For a sphere, eigenvalues should be roughly equal, so s ≈ 1
    # Allow some tolerance due to sampling noise
    assert 0.8 <= s <= 1.0, f"Spherical halo should have s ≈ 1, but got {s}"
    assert np.isfinite(s), "Shape parameter must be finite"


def test_inertia_tensor_single_particle():
    """
    Verify handling of edge case: single particle.
    Shape should be 0 or handled gracefully.
    """
    positions = np.array([[0.0, 0.0, 0.0]])
    masses = np.array([1.0])
    
    halo_data = {
        'particle_positions': positions,
        'particle_masses': masses
    }
    
    # This should not crash, though the result might be 0 or NaN depending on implementation
    # We expect it to handle this gracefully (e.g., return 0.0 or raise a specific warning)
    try:
        results = compute_halo_metrics(halo_data)
        s = results['shape']
        # If it returns a value, it should be valid
        assert np.isfinite(s) or s == 0.0, "Single particle shape should be finite or 0"
    except Exception as e:
        # If it raises, it should be a specific error, not a generic crash
        assert isinstance(e, (ValueError, RuntimeError)), f"Unexpected error type: {type(e)}"


def test_spin_parameter_subsample():
    """
    T019: Verify spin parameter calculation on a subsample.
    """
    # Mock data
    N = 500
    np.random.seed(42)
    # Positions
    r = np.random.rand(N, 3) * 10
    # Velocities
    v = np.random.rand(N, 3) * 10
    masses = np.ones(N)
    
    halo_data = {
        'particle_positions': r,
        'particle_masses': masses,
        'particle_velocities': v
    }
    
    results = compute_halo_metrics(halo_data)
    lambda_val = results['spin']
    
    # Just check it's a finite number
    assert np.isfinite(lambda_val), "Spin parameter is not finite"
    # Spin parameter is typically small (0.01 - 0.1), but can be up to ~1
    assert 0 <= lambda_val <= 10, f"Spin parameter {lambda_val} seems unphysically large"


def test_nfw_convergence():
    """
    T020: Verify NFW profile fitting convergence.
    """
    from scipy.optimize import curve_fit
    
    def nfw_profile(r, rs, rho_s):
        # Avoid division by zero
        r = np.maximum(r, 1e-8)
        return rho_s / (r/rs * (1 + r/rs)**2)
    
    r = np.logspace(-1, 1, 50)
    true_rs, true_rho_s = 10.0, 1.0
    rho = nfw_profile(r, true_rs, true_rho_s)
    rho += np.random.normal(0, 0.01, size=r.shape)  # Add noise
    
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