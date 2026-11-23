"""
Unit tests for Minkowski Functional computation.
"""
import pytest
import numpy as np
import healpy as hp
from pathlib import Path
import json
import os

# Add parent directory to path if needed
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.minkowski import compute_minkowski_functionals, apply_schmalzing_gorski_correction

@pytest.fixture
def sample_map_and_mask():
    """Create a sample HEALPix map and mask for testing."""
    nside = 16
    npix = hp.nside2npix(nside)
    
    # Create a simple Gaussian random field
    np.random.seed(42)
    cmb_map = np.random.normal(0, 1, npix)
    
    # Create a simple mask (all valid)
    mask = np.ones(npix, dtype=int)
    
    return cmb_map, mask, nside

def test_compute_minkowski_functionals_basic(sample_map_and_mask):
    """Test basic computation of Minkowski Functionals."""
    cmb_map, mask, nside = sample_map_and_mask
    thresholds = [0.0, 1.0, -1.0]
    
    results = compute_minkowski_functionals(cmb_map, mask, thresholds)
    
    # Check that results are returned
    assert isinstance(results, dict)
    assert len(results) == len(thresholds)
    
    # Check that each result has the expected keys
    for thresh, mf_values in results.items():
        assert "area" in mf_values
        assert "perimeter" in mf_values
        assert "genus" in mf_values
        
        # Check that values are floats
        assert isinstance(mf_values["area"], float)
        assert isinstance(mf_values["perimeter"], float)
        assert isinstance(mf_values["genus"], float)
        
        # Check that area is between 0 and 1
        assert 0 <= mf_values["area"] <= 1
        
        # Check that perimeter is non-negative
        assert mf_values["perimeter"] >= 0

def test_apply_schmalzing_gorski_correction(sample_map_and_mask):
    """Test Schmalzing & Gorski correction."""
    cmb_map, mask, nside = sample_map_and_mask
    thresholds = [0.0]
    
    # Compute observed MFs
    observed_mfs = compute_minkowski_functionals(cmb_map, mask, thresholds)
    
    # Apply correction
    corrected_mfs = apply_schmalzing_gorski_correction(observed_mfs, mask)
    
    # Check that corrected MFs are returned
    assert isinstance(corrected_mfs, dict)
    assert len(corrected_mfs) == len(thresholds)
    
    # Check that each result has the expected keys
    for thresh, mf_values in corrected_mfs.items():
        assert "area" in mf_values
        assert "perimeter" in mf_values
        assert "genus" in mf_values
        
        # Check that values are floats
        assert isinstance(mf_values["area"], float)
        assert isinstance(mf_values["perimeter"], float)
        assert isinstance(mf_values["genus"], float)

def test_compute_minkowski_functionals_with_mask():
    """Test computation with a masked region."""
    nside = 16
    npix = hp.nside2npix(nside)
    
    # Create a sample map
    np.random.seed(42)
    cmb_map = np.random.normal(0, 1, npix)
    
    # Create a mask with some invalid pixels
    mask = np.ones(npix, dtype=int)
    mask[0:10] = 0  # Mask first 10 pixels
    
    thresholds = [0.0]
    
    results = compute_minkowski_functionals(cmb_map, mask, thresholds)
    
    # Check that results are returned
    assert isinstance(results, dict)
    assert len(results) == 1
    
    # Check that values are reasonable
    mf_values = results[0.0]
    assert 0 <= mf_values["area"] <= 1
    assert mf_values["perimeter"] >= 0

def test_compute_minkowski_functionals_zero_std():
    """Test that a map with zero std raises an error."""
    nside = 16
    npix = hp.nside2npix(nside)
    
    # Create a map with zero std
    cmb_map = np.ones(npix)
    mask = np.ones(npix, dtype=int)
    
    thresholds = [0.0]
    
    with pytest.raises(ValueError, match="Standard deviation is zero"):
        compute_minkowski_functionals(cmb_map, mask, thresholds)

def test_compute_minkowski_functionals_no_valid_pixels():
    """Test that a map with no valid pixels raises an error."""
    nside = 16
    npix = hp.nside2npix(nside)
    
    # Create a map
    cmb_map = np.random.normal(0, 1, npix)
    
    # Create a mask with no valid pixels
    mask = np.zeros(npix, dtype=int)
    
    thresholds = [0.0]
    
    with pytest.raises(ValueError, match="No valid pixels in the mask"):
        compute_minkowski_functionals(cmb_map, mask, thresholds)
