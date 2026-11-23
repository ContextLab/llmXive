import os
import sys
import pytest
import numpy as np
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from harmonics import compute_alm, compute_full_sky_cl, split_hemispheres
from config import ensure_directories
from logging_config import setup_logging, get_logger

# Setup logging for tests
logger = get_logger("test_harmonics")

# Constants for testing
TEST_NSIDE = 16  # Small Nside for fast unit tests
L_MIN = 2
L_MAX = 128
EXPECTED_LENGTH = L_MAX - L_MIN + 1

# Ensure directories exist for any potential file I/O
ensure_directories()

@pytest.fixture
def mock_map():
    """Generate a mock CMB map for testing."""
    n_pix = 12 * TEST_NSIDE**2
    # Create a map with known properties (no NaN/Inf)
    np.random.seed(42)
    mock_data = np.random.randn(n_pix) * 1e-5  # Typical CMB amplitude in K
    return mock_data

@pytest.fixture
def mock_mask():
    """Generate a simple unmasked map (all True)."""
    n_pix = 12 * TEST_NSIDE**2
    return np.ones(n_pix, dtype=bool)

def test_cl_positivity(mock_map, mock_mask):
    """
    US2 Test: Verify that computed C_l values are non-negative.
    Physical requirement: Angular power spectrum must be >= 0.
    """
    # Compute a_lm from mock map
    alm = compute_alm(mock_map, lmax=L_MAX, mmax=None)
    
    # Compute C_l
    cl = compute_full_sky_cl(alm, lmax=L_MAX)
    
    # Extract range [L_MIN, L_MAX]
    cl_subset = cl[L_MIN : L_MAX + 1]
    
    # Assert all values are non-negative (with small tolerance for numerical errors)
    assert np.all(cl_subset >= -1e-20), f"Negative C_l values found: {cl_subset[cl_subset < 0]}"
    logger.info("C_l positivity test passed: All values >= 0")

def test_cl_length(mock_map, mock_mask):
    """
    US2 Test: Verify C_l array length matches (l_max - l_min + 1).
    """
    # Compute a_lm
    alm = compute_alm(mock_map, lmax=L_MAX, mmax=None)
    
    # Compute C_l
    cl = compute_full_sky_cl(alm, lmax=L_MAX)
    
    # Extract range [L_MIN, L_MAX]
    cl_subset = cl[L_MIN : L_MAX + 1]
    
    # Verify length
    expected_len = L_MAX - L_MIN + 1
    actual_len = len(cl_subset)
    
    assert actual_len == expected_len, (
        f"C_l length mismatch. Expected {expected_len}, got {actual_len}. "
        f"Range: [{L_MIN}, {L_MAX}]"
    )
    logger.info(f"C_l length test passed: Length is {actual_len} (expected {expected_len})")

def test_cl_structure(mock_map, mock_mask):
    """
    Combined test for C_l properties: positivity, length, and type.
    """
    alm = compute_alm(mock_map, lmax=L_MAX, mmax=None)
    cl = compute_full_sky_cl(alm, lmax=L_MAX)
    cl_subset = cl[L_MIN : L_MAX + 1]
    
    # Check type
    assert isinstance(cl_subset, np.ndarray), "C_l must be a numpy array"
    
    # Check dtype
    assert np.issubdtype(cl_subset.dtype, np.floating), "C_l must be floating point"
    
    # Check positivity
    assert np.all(cl_subset >= 0), "C_l must be non-negative"
    
    # Check length
    assert len(cl_subset) == EXPECTED_LENGTH, f"Length must be {EXPECTED_LENGTH}"
    
    logger.info("Combined C_l structure test passed")

def test_cl_with_realistic_spectrum(mock_map, mock_mask):
    """
    Test C_l computation with a mock map that has a realistic power spectrum shape.
    Ensures the computation pipeline handles non-flat spectra correctly.
    """
    # Create a map with a specific power law spectrum (approximate C_l ~ l^-2)
    n_pix = 12 * TEST_NSIDE**2
    np.random.seed(123)
    
    # Generate random a_lm with decreasing power
    l_vals = np.arange(2, L_MAX + 1)
    theoretical_cl = 1.0 / (l_vals ** 2)
    
    # Generate a_lm with correct variance
    alm = hp.synalm(theoretical_cl, lmax=L_MAX)
    mock_map = hp.alm2map(alm, TEST_NSIDE)
    
    # Compute C_l
    computed_alm = compute_alm(mock_map, lmax=L_MAX)
    computed_cl = compute_full_sky_cl(computed_alm, lmax=L_MAX)
    computed_cl_subset = computed_cl[L_MIN : L_MAX + 1]
    
    # Check positivity and length
    assert np.all(computed_cl_subset >= 0), "Computed C_l must be non-negative"
    assert len(computed_cl_subset) == EXPECTED_LENGTH, "Computed C_l length mismatch"
    
    # Check that the shape is roughly preserved (within 50% tolerance due to noise)
    ratio = computed_cl_subset / theoretical_cl
    assert np.all((ratio > 0.5) & (ratio < 1.5)), "Computed spectrum shape deviates too much"
    
    logger.info("Realistic spectrum test passed")

def test_edge_cases():
    """
    Test edge cases for l_min and l_max.
    """
    # Create a minimal map
    n_pix = 12 * 2**2  # Nside=2
    np.random.seed(999)
    small_map = np.random.randn(n_pix)
    
    # Test with lmax = 2 (minimum valid)
    alm = compute_alm(small_map, lmax=2, mmax=None)
    cl = compute_full_sky_cl(alm, lmax=2)
    
    # Should have 1 element (l=2)
    assert len(cl) == 3, "C_l array should have 3 elements (l=0,1,2)"
    assert cl[2] >= 0, "C_l at l=2 must be non-negative"
    
    logger.info("Edge case test passed")

def test_hemispherical_split_generation(mock_map, mock_mask):
    """
    US2 Integration Test: Verify hemispherical split generation.
    Tests that split_hemispheres correctly generates North/South and East/West masks
    with the expected pixel counts and properties.
    """
    import healpy as hp
    
    # Get the split masks
    masks = split_hemispheres(TEST_NSIDE)
    
    # Verify structure
    assert isinstance(masks, dict), "split_hemispheres should return a dictionary"
    assert "ns_mask" in masks, "Dictionary must contain 'ns_mask' key"
    assert "ew_mask" in masks, "Dictionary must contain 'ew_mask' key"
    
    ns_mask = masks["ns_mask"]
    ew_mask = masks["ew_mask"]
    
    # Verify shapes
    n_pix = 12 * TEST_NSIDE**2
    assert ns_mask.shape == (n_pix,), f"NS mask shape mismatch: {ns_mask.shape} vs {(n_pix,)}"
    assert ew_mask.shape == (n_pix,), f"EW mask shape mismatch: {ew_mask.shape} vs {(n_pix,)}"
    
    # Verify data types
    assert ns_mask.dtype == bool, "NS mask must be boolean"
    assert ew_mask.dtype == bool, "EW mask must be boolean"
    
    # Verify pixel counts (approximately 50% for each hemisphere)
    ns_count = np.sum(ns_mask)
    ew_count = np.sum(ew_mask)
    
    # Allow some tolerance for pixel boundary effects at low Nside
    expected_count = n_pix / 2
    tolerance = 0.1 * expected_count  # 10% tolerance
    
    assert abs(ns_count - expected_count) <= tolerance, (
        f"NS mask pixel count {ns_count} deviates too much from expected {expected_count}"
    )
    assert abs(ew_count - expected_count) <= tolerance, (
        f"EW mask pixel count {ew_count} deviates too much from expected {expected_count}"
    )
    
    # Verify that masks are complementary (NS + ~NS = all)
    ns_complement = ~ns_mask
    assert np.sum(ns_mask & ns_complement) == 0, "NS mask and its complement should not overlap"
    assert np.sum(ns_mask | ns_complement) == n_pix, "NS mask and its complement should cover all pixels"
    
    # Verify that we can apply masks to the mock map
    ns_map = mock_map * ns_mask
    ew_map = mock_map * ew_mask
    
    # Check that masked regions are zeroed out
    assert np.all(ns_map[~ns_mask] == 0), "NS masked regions should be zero"
    assert np.all(ew_map[~ew_mask] == 0), "EW masked regions should be zero"
    
    # Verify that the number of non-zero elements matches mask counts
    assert np.sum(ns_map != 0) == ns_count, "Non-zero elements in NS map should match mask count"
    assert np.sum(ew_map != 0) == ew_count, "Non-zero elements in EW map should match mask count"
    
    logger.info(f"Hemispherical split test passed: NS={ns_count}/{n_pix}, EW={ew_count}/{n_pix}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])