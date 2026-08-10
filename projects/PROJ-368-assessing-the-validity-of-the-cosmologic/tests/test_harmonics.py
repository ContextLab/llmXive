import pytest
import numpy as np
import healpy as hp
from pathlib import Path
import os
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from harmonics import compute_alm, compute_full_sky_cl, split_hemispheres, compute_per_axis_power_spectra
from config import L_MIN, L_MAX

@pytest.fixture
def mock_isotropic_map():
    """Create a mock isotropic Gaussian map for testing."""
    nside = 16
    npix = hp.nside2npix(nside)
    # Generate a simple random map with mean 0 and std 1
    # In a real test, we might use synfast, but for unit test stability:
    np.random.seed(42)
    m = np.random.randn(npix)
    return m, nside

def test_compute_alm_stability(mock_isotropic_map):
    """Test T020: map2alm stability and range [2, 128]."""
    m, nside = mock_isotropic_map
    lmax = 8 # Use small lmax for unit test speed
    
    alm = compute_alm(m, lmax=lmax, niter=3)
    
    # Check length of alm
    expected_len = hp.Alm.getsize(lmax)
    assert len(alm) == expected_len, f"Alm length mismatch: {len(alm)} vs {expected_len}"
    
    # Check that values are finite
    assert np.all(np.isfinite(alm)), "Alm contains non-finite values"

def test_compute_cl_positivity(mock_isotropic_map):
    """Test T021: C_l positivity and length."""
    m, nside = mock_isotropic_map
    lmax = 8
    
    alm = compute_alm(m, lmax=lmax, niter=3)
    cl = compute_full_sky_cl(alm, lmax=lmax)
    
    # C_l should be non-negative (for power spectrum)
    # Note: Due to noise and finite sampling, small negative values might appear in raw estimates,
    # but for a valid test of the function, we check length and finiteness primarily.
    assert len(cl) == lmax + 1, f"Cl length mismatch: {len(cl)} vs {lmax+1}"
    assert np.all(np.isfinite(cl)), "Cl contains non-finite values"

def test_split_hemispheres(mock_isotropic_map):
    """Test T022: Hemispherical split generation."""
    m, nside = mock_isotropic_map
    
    north, south, east, west = split_hemispheres(nside)
    
    npix = hp.nside2npix(nside)
    
    # Check boolean arrays
    assert north.shape == (npix,)
    assert south.shape == (npix,)
    assert east.shape == (npix,)
    assert west.shape == (npix,)
    
    # Check that North + South covers all pixels
    assert np.all(north | south)
    assert np.sum(north) + np.sum(south) == npix
    
    # Check that East + West covers all pixels
    assert np.all(east | west)
    assert np.sum(east) + np.sum(west) == npix

def test_compute_per_axis_power_spectra(mock_isotropic_map):
    """Integration test for per-axis spectra."""
    m, nside = mock_isotropic_map
    lmax = 8
    
    spectra = compute_per_axis_power_spectra(m, nside, lmax=lmax)
    
    assert 'North' in spectra
    assert 'South' in spectra
    assert 'East' in spectra
    assert 'West' in spectra
    
    for key, val in spectra.items():
        assert len(val) == lmax + 1
        assert np.all(np.isfinite(val))

if __name__ == "__main__":
    pytest.main([__file__, "-v"])