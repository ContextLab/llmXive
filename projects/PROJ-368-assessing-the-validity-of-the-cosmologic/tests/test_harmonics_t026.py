import numpy as np
import healpy as hp
import pytest
import os
from pathlib import Path

from harmonics import compute_hemisphere_cl, split_hemispheres

def test_split_hemispheres_z_axis():
    """Test North/South split generation."""
    nside = 16
    mask_n, mask_s = split_hemispheres(nside, axis='z')
    
    assert len(mask_n) == hp.nside2npix(nside)
    assert len(mask_s) == hp.nside2npix(nside)
    assert np.all(mask_n | mask_s)  # All pixels covered
    assert np.sum(mask_n) > 0
    assert np.sum(mask_s) > 0

def test_split_hemispheres_x_axis():
    """Test East/West split generation."""
    nside = 16
    mask_e, mask_w = split_hemispheres(nside, axis='x')
    
    assert len(mask_e) == hp.nside2npix(nside)
    assert len(mask_w) == hp.nside2npix(nside)
    assert np.all(mask_e | mask_w)  # All pixels covered
    assert np.sum(mask_e) > 0
    assert np.sum(mask_w) > 0

def test_compute_hemisphere_cl_structure():
    """Test that compute_hemisphere_cl returns expected structure."""
    nside = 16
    npix = hp.nside2npix(nside)
    
    # Create a simple test map (all ones)
    test_map = np.ones(npix)
    
    result = compute_hemisphere_cl(test_map, nside, axis='z', lmin=2, lmax=10)
    
    assert 'north' in result
    assert 'south' in result
    assert len(result['north']) == 10 - 2 + 1  # l=2 to l=10
    assert len(result['south']) == 10 - 2 + 1
    assert np.all(result['north'] >= 0)  # Power spectrum should be non-negative
    assert np.all(result['south'] >= 0)

def test_compute_hemisphere_cl_east_west():
    """Test East/West hemispherical C_l computation."""
    nside = 16
    npix = hp.nside2npix(nside)
    
    test_map = np.ones(npix)
    
    result = compute_hemisphere_cl(test_map, nside, axis='x', lmin=2, lmax=10)
    
    assert 'east' in result
    assert 'west' in result
    assert len(result['east']) == 10 - 2 + 1
    assert len(result['west']) == 10 - 2 + 1

def test_hemisphere_cl_symmetry():
    """Test that for a uniform map, hemispherical spectra are similar."""
    nside = 16
    npix = hp.nside2npix(nside)
    
    # Uniform map
    test_map = np.ones(npix)
    
    result = compute_hemisphere_cl(test_map, nside, axis='z', lmin=2, lmax=10)
    
    # For a uniform map, the power spectrum should be very similar in both hemispheres
    # (allowing for some numerical differences)
    diff = np.abs(result['north'] - result['south'])
    # The difference should be small relative to the values
    if np.mean(result['north']) > 0:
        rel_diff = diff / np.mean(result['north'])
        assert np.mean(rel_diff) < 0.1, f"Relative difference too large: {np.mean(rel_diff)}"
