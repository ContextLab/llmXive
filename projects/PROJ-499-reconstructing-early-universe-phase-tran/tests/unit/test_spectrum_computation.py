"""
Unit tests for spectrum_computation module.
"""
import os
import tempfile
import numpy as np
import healpy as hp
import pytest
from unittest.mock import patch, MagicMock

# Import the module to test
# Assuming the module is in the code directory and we are running from project root
# We need to add the code directory to the path if running as a script
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from spectrum_computation import validate_sky_coverage, compute_bb_spectrum

def create_test_mask(nside, coverage=0.8):
    """Helper to create a temporary mask file with specified coverage."""
    npix = hp.nside2npix(nside)
    target_valid = int(npix * coverage)
    mask = np.zeros(npix)
    mask[:target_valid] = 1.0
    # Shuffle to make it look more like a real mask
    np.random.shuffle(mask)
    
    fd, path = tempfile.mkstemp(suffix='.fits')
    hp.write_map(path, mask, nest=True)
    os.close(fd)
    return path, mask

def test_validate_sky_coverage_pass():
    """Test that validation passes when coverage >= 0.70."""
    nside = 32
    path, _ = create_test_mask(nside, coverage=0.80)
    try:
        coverage = validate_sky_coverage(path, nside=nside)
        assert coverage >= 0.70
        assert abs(coverage - 0.80) < 0.01
    finally:
        os.remove(path)

def test_validate_sky_coverage_fail():
    """Test that validation raises ValueError when coverage < 0.70."""
    nside = 32
    path, _ = create_test_mask(nside, coverage=0.50)
    try:
        with pytest.raises(ValueError, match="Sky coverage .* is below the required threshold of 0.70"):
            validate_sky_coverage(path, nside=nside)
    finally:
        os.remove(path)

def test_validate_sky_coverage_boundary():
    """Test validation at exactly 0.70 coverage."""
    nside = 64
    # 0.70 is the threshold, so it should pass
    path, _ = create_test_mask(nside, coverage=0.70)
    try:
        coverage = validate_sky_coverage(path, nside=nside)
        assert coverage >= 0.70
    finally:
        os.remove(path)

def test_validate_sky_coverage_file_not_found():
    """Test that FileNotFoundError is raised if mask file does not exist."""
    with pytest.raises(FileNotFoundError):
        validate_sky_coverage("nonexistent_mask.fits")

def test_compute_bb_spectrum_basic():
    """Test basic spectrum computation with a simple map."""
    nside = 16
    npix = hp.nside2npix(nside)
    
    # Create simple Q and U maps
    q = np.random.randn(npix)
    u = np.random.randn(npix)
    
    fd_map, map_path = tempfile.mkstemp(suffix='.fits')
    # Write [Q, U] as a list of maps
    hp.write_map(map_path, [q, u], nest=True)
    os.close(fd_map)
    
    try:
        result = compute_bb_spectrum(map_path)
        
        assert "l_values" in result
        assert "cl_bb_values" in result
        assert result["nside"] == nside
        assert len(result["l_values"]) == len(result["cl_bb_values"])
        # lmax should be 2*nside - 2
        expected_lmax = 2 * nside - 2
        assert result["lmax"] == expected_lmax
    finally:
        os.remove(map_path)

def test_compute_bb_spectrum_with_mask():
    """Test spectrum computation with a mask applied."""
    nside = 16
    npix = hp.nside2npix(nside)
    
    q = np.random.randn(npix)
    u = np.random.randn(npix)
    
    # Create a mask
    mask = np.ones(npix)
    mask[:npix//2] = 0.0 # Mask half the sky
    
    fd_map, map_path = tempfile.mkstemp(suffix='.fits')
    fd_mask, mask_path = tempfile.mkstemp(suffix='.fits')
    
    hp.write_map(map_path, [q, u], nest=True)
    hp.write_map(mask_path, mask, nest=True)
    
    os.close(fd_map)
    os.close(fd_mask)
    
    try:
        result = compute_bb_spectrum(map_path, mask_path)
        
        assert "l_values" in result
        assert "cl_bb_values" in result
        # The values should be computed, though with a mask they might be noisy
    finally:
        os.remove(map_path)
        os.remove(mask_path)