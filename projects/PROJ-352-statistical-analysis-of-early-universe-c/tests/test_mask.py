"""
Unit tests for mask application functionality.

These tests verify:
1. Mask loading from files
2. Mask application to CMB maps
3. Buffer zone application
4. Output file generation
"""
import os
import json
import tempfile
import numpy as np
import healpy as hp
import pytest
from pathlib import Path

from mask import load_mask, apply_mask, apply_buffer_zone, save_masked_map

# Create a temporary directory for test outputs
@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_cmb_map(nside=128):
    """Generate a sample CMB map for testing."""
    npix = 12 * nside**2
    # Create a simple Gaussian random field
    np.random.seed(42)
    return np.random.normal(0, 100, npix).astype(np.float32)

@pytest.fixture
def sample_mask(nside=128):
    """Create a sample mask with some masked regions."""
    npix = 12 * nside**2
    mask = np.ones(npix, dtype=np.float64)
    # Mask a band around the equator (Galactic plane approximation)
    theta, phi = hp.pix2ang(nside, np.arange(npix), nest=True)
    # Mask pixels within 20 degrees of the equator (theta ~ pi/2)
    mask[np.abs(theta - np.pi/2) < np.deg2rad(20)] = 0
    return mask

def test_apply_mask(sample_cmb_map, sample_mask):
    """Test that apply_mask correctly zeros out masked pixels."""
    masked_map = apply_mask(sample_cmb_map, sample_mask)

    # Check that masked pixels are zero
    masked_indices = np.where(sample_mask == 0)[0]
    assert np.all(masked_map[masked_indices] == 0), "Masked pixels should be zero"

    # Check that unmasked pixels retain their values
    unmasked_indices = np.where(sample_mask == 1)[0]
    assert np.all(masked_map[unmasked_indices] == sample_cmb_map[unmasked_indices]), \
        "Unmasked pixels should retain their values"

def test_apply_buffer_zone(sample_mask, temp_dir):
    """Test that buffer zone correctly extends masked regions."""
    nside = hp.get_nside(sample_mask)
    buffered_mask = apply_buffer_zone(sample_mask, nside, buffer_pixels=2)

    # The buffered mask should have more masked pixels than the original
    original_masked = np.sum(sample_mask == 0)
    buffered_masked = np.sum(buffered_mask == 0)
    assert buffered_masked >= original_masked, \
        "Buffered mask should have at least as many masked pixels"

    # All originally masked pixels should still be masked
    original_masked_indices = np.where(sample_mask == 0)[0]
    assert np.all(buffered_mask[original_masked_indices] == 0), \
        "Originally masked pixels should remain masked"

    # Check that some previously unmasked pixels are now masked
    # (unless the mask already covered everything)
    if original_masked < len(sample_mask):
        # There should be at least some pixels that were unmasked but are now masked
        newly_masked = np.sum((sample_mask == 1) & (buffered_mask == 0))
        assert newly_masked > 0, \
            "Buffer zone should mask some previously unmasked pixels"

def test_mask_dimensions_match(sample_cmb_map, sample_mask):
    """Test that mask and CMB map must have the same dimensions."""
    # Create a mask with wrong dimensions
    wrong_mask = np.ones(len(sample_cmb_map) - 10, dtype=np.float64)

    with pytest.raises(ValueError):
        apply_mask(sample_cmb_map, wrong_mask)

def test_save_masked_map(sample_cmb_map, sample_mask, temp_dir):
    """Test saving a masked map to a FITS file."""
    masked_map = apply_mask(sample_cmb_map, sample_mask)
    output_path = temp_dir / "test_masked_map.fits"

    save_masked_map(masked_map, output_path, nside=128)

    # Check that the file was created
    assert output_path.exists(), "Output FITS file should be created"

    # Check that the file can be read back
    loaded_map = hp.read_map(str(output_path), field=0, nest=True)
    assert np.allclose(loaded_map, masked_map), "Loaded map should match saved map"

def test_buffer_zone_edge_cases(sample_mask, temp_dir):
    """Test buffer zone with edge cases."""
    nside = hp.get_nside(sample_mask)

    # Test with buffer_pixels=0 (should be same as original mask)
    no_buffer_mask = apply_buffer_zone(sample_mask, nside, buffer_pixels=0)
    assert np.array_equal(no_buffer_mask, sample_mask), \
        "Buffer of 0 should not change the mask"

    # Test with very large buffer (should mask almost everything)
    large_buffer_mask = apply_buffer_zone(sample_mask, nside, buffer_pixels=10)
    large_masked = np.sum(large_buffer_mask == 0)
    assert large_masked > np.sum(sample_mask == 0), \
        "Large buffer should mask more pixels"