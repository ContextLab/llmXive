import pytest
import numpy as np
import healpy as hp
from pathlib import Path
import json
import tempfile
import os

from mask import apply_schmalzing_gorski_correction, apply_buffer_zone, apply_mask, load_mask

@pytest.fixture
def sample_mask_n128():
    """Create a sample mask with Nside=128 for testing."""
    nside = 128
    npixels = 12 * nside ** 2
    # Create a simple mask: unmask a circular region around the North Pole
    mask = np.ones(npixels)
    theta = np.linspace(0, np.pi, npixels)
    # Mask out regions with theta > pi/3 (i.e., keep only the North Pole cap)
    mask[theta > np.pi/3] = 0.0
    return mask, nside

def test_schmalzing_gorski_correction_basic(sample_mask_n128):
    """Test that Schmalzing & Gorski correction returns expected structure."""
    mask, nside = sample_mask_n128
    result = apply_schmalzing_gorski_correction(mask, nside)
    
    # Check that all required keys are present
    required_keys = ['analytical_coverage', 'actual_coverage', 'difference', 
                    'nside', 'total_pixels', 'valid_pixels']
    for key in required_keys:
        assert key in result, f"Missing key: {key}"
    
    # Check types
    assert isinstance(result['analytical_coverage'], float)
    assert isinstance(result['actual_coverage'], float)
    assert isinstance(result['difference'], float)
    assert isinstance(result['nside'], int)
    assert isinstance(result['total_pixels'], int)
    assert isinstance(result['valid_pixels'], int)
    
    # Check consistency
    assert result['nside'] == nside
    expected_total = 12 * nside ** 2
    assert result['total_pixels'] == expected_total
    assert result['valid_pixels'] == int(np.sum(mask > 0.5))
    
    # Check that actual coverage matches calculation
    expected_actual = result['valid_pixels'] / result['total_pixels']
    assert abs(result['actual_coverage'] - expected_actual) < 1e-10

def test_schmalzing_gorski_difference_is_zero(sample_mask_n128):
    """Test that the difference between analytical and actual coverage is zero 
    (since we use pixel count as the analytical expectation)."""
    mask, nside = sample_mask_n128
    result = apply_schmalzing_gorski_correction(mask, nside)
    
    # In our implementation, analytical_coverage == actual_coverage
    assert abs(result['difference']) < 1e-10, "Difference should be zero"

def test_buffer_zone_reduces_coverage(sample_mask_n128):
    """Test that applying a buffer zone reduces the number of unmasked pixels."""
    mask, nside = sample_mask_n128
    original_coverage = np.sum(mask > 0.5) / (12 * nside ** 2)
    
    buffered_mask = apply_buffer_zone(mask, nside, buffer_pixels=2)
    buffered_coverage = np.sum(buffered_mask > 0.5) / (12 * nside ** 2)
    
    # Buffer zone should reduce or maintain coverage, never increase
    assert buffered_coverage <= original_coverage, "Buffer zone should not increase coverage"
    
    # If there are any masked pixels, the buffer should reduce coverage
    if np.sum(mask <= 0.5) > 0:
        assert buffered_coverage < original_coverage, "Buffer zone should reduce coverage when masked regions exist"

def test_schmalzing_gorski_with_full_mask(sample_mask_n128):
    """Test Schmalzing & Gorski correction with a fully unmasked map."""
    mask, nside = sample_mask_n128
    full_mask = np.ones_like(mask)
    
    result = apply_schmalzing_gorski_correction(full_mask, nside)
    
    assert result['actual_coverage'] == 1.0
    assert result['analytical_coverage'] == 1.0
    assert result['difference'] == 0.0
    assert result['valid_pixels'] == result['total_pixels']

def test_schmalzing_gorski_with_empty_mask(sample_mask_n128):
    """Test Schmalzing & Gorski correction with a fully masked map."""
    mask, nside = sample_mask_n128
    empty_mask = np.zeros_like(mask)
    
    result = apply_schmalzing_gorski_correction(empty_mask, nside)
    
    assert result['actual_coverage'] == 0.0
    assert result['analytical_coverage'] == 0.0
    assert result['difference'] == 0.0
    assert result['valid_pixels'] == 0

def test_schmalzing_gorski_report_serialization(sample_mask_n128):
    """Test that the correction result can be serialized to JSON."""
    mask, nside = sample_mask_n128
    result = apply_schmalzing_gorski_correction(mask, nside)
    
    # Should not raise an exception
    json_str = json.dumps(result)
    parsed = json.loads(json_str)
    
    # Verify all keys are preserved
    for key in result:
        assert key in parsed
        assert result[key] == parsed[key]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])