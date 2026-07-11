"""
Unit tests for anisotropy module.
"""
import pytest
import numpy as np
from src.anisotropy import generate_healpix_map, fit_dipole_coefficients, calculate_anisotropy_stats

def test_generate_healpix_map_empty():
    """Test that an empty event list returns NaN maps."""
    counts, exposure, intensity = generate_healpix_map([], nside=64)
    assert np.all(np.isnan(counts))
    assert np.all(np.isnan(exposure))
    assert np.all(np.isnan(intensity))

def test_generate_healpix_map_single_event():
    """Test map generation with a single event."""
    events = [{'ra': 0.0, 'dec': 0.0}]
    counts, exposure, intensity = generate_healpix_map(events, nside=64)
    
    assert np.any(counts > 0)
    assert np.sum(counts) == 1
    # Intensity should be normalized, so mean of non-NaN should be 1
    valid_intensity = intensity[~np.isnan(intensity)]
    assert len(valid_intensity) > 0
    assert np.isclose(np.mean(valid_intensity), 1.0)

def test_generate_healpix_map_uniform():
    """Test map generation with uniform distribution."""
    # Create 1000 events uniformly distributed
    np.random.seed(42)
    n_events = 1000
    ras = np.random.uniform(0, 2 * np.pi, n_events)
    decs = np.random.uniform(-np.pi/2, np.pi/2, n_events)
    
    events = [{'ra': r, 'dec': d} for r, d in zip(ras, decs)]
    counts, exposure, intensity = generate_healpix_map(events, nside=32) # Lower res for speed
    
    # For uniform distribution, intensity should be close to 1 everywhere
    valid_intensity = intensity[~np.isnan(intensity)]
    assert np.isclose(np.mean(valid_intensity), 1.0, atol=0.1)

def test_fit_dipole_coefficients():
    """Test dipole fitting with a known dipole signal."""
    # Create a map with a known dipole
    nside = 64
    npix = hp.nside2npix(nside)
    theta = np.pi / 2 - np.arcsin(np.linspace(-1, 1, npix)) # Not exactly uniform
    # Simpler: generate a map with a dipole pattern
    # Intensity = 1 + A * cos(theta)
    # But we need to pass events, not a map.
    # So we generate events with a dipole bias.
    
    # Generate events with a dipole in RA=0, Dec=0
    n_events = 5000
    np.random.seed(123)
    # Isotropic base
    u = np.random.uniform(-1, 1, n_events)
    v = np.random.uniform(0, 1, n_events)
    dec_base = np.arcsin(u)
    ra_base = 2 * np.pi * v
    
    # Apply dipole modulation: weight by (1 + 0.1 * cos(ra))
    # This is a simplified model
    weights = 1 + 0.1 * np.cos(ra_base)
    
    # Resample events based on weights
    indices = np.random.choice(n_events, size=n_events, p=weights/np.sum(weights))
    ras = ra_base[indices]
    decs = dec_base[indices]
    
    events = [{'ra': r, 'dec': d} for r, d in zip(ras, decs)]
    
    counts, exposure, intensity_map = generate_healpix_map(events, nside=nside)
    coeffs = fit_dipole_coefficients(intensity_map, nside=nside)
    
    assert 'dipole_amplitude' in coeffs
    assert 'dipole_phase' in coeffs
    assert coeffs['dipole_amplitude'] > 0
    assert 0 <= coeffs['dipole_phase'] < 2 * np.pi

def test_calculate_anisotropy_stats():
    """Test the high-level stats function."""
    events = [
        {'ra': 0.0, 'dec': 0.0},
        {'ra': 1.0, 'dec': 0.5},
        {'ra': 2.0, 'dec': -0.5}
    ]
    stats = calculate_anisotropy_stats(events, nside=64)
    
    assert 'dipole_amplitude' in stats
    assert 'dipole_phase' in stats
    assert 'quadrupole_amplitude' in stats
    assert isinstance(stats['dipole_amplitude'], float)
