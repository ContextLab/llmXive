"""
Unit tests for mask generation functions.

This module contains tests for User Story 1, specifically verifying that
generated gap masks match the target gap fraction within a tolerance of ±0.5%.
"""
import pytest
import numpy as np
import healpy as hp
import os
import sys

# Add the code directory to the path to allow imports from sibling modules
# assuming the project structure is:
# code/simulation/
# tests/unit/
# We need to import from code/simulation/utils.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from simulation.utils import generate_random_mask, generate_clustered_mask


def _create_empty_map(nside: int) -> np.ndarray:
    """Create an empty Healpix map with the given nside."""
    return np.zeros(hp.nside2npix(nside))


def _calculate_gap_fraction(mask: np.ndarray) -> float:
    """Calculate the fraction of masked pixels in a boolean mask."""
    return np.mean(mask)


@pytest.mark.parametrize("gap_fraction", [0.05, 0.10, 0.15, 0.20, 0.30])
def test_gap_fraction_tolerance_random(gap_fraction: float):
    """
    Test that generated random masks match the target gap fraction within ±0.5%.
    
    This test uses a fixed seed to ensure reproducibility while verifying
    that the mask generation logic correctly approximates the target fraction.
    """
    nside = 512
    target_fraction = gap_fraction
    tolerance = 0.005  # ±0.5%
    
    # Generate mask with fixed seed for reproducibility
    mask = generate_random_mask(nside, target_fraction, seed=42)
    
    actual_fraction = _calculate_gap_fraction(mask)
    deviation = abs(actual_fraction - target_fraction)
    
    assert deviation <= tolerance, (
        f"Random mask gap fraction deviation too large: "
        f"target={target_fraction:.4f}, actual={actual_fraction:.4f}, "
        f"deviation={deviation:.4f}, tolerance={tolerance}"
    )


@pytest.mark.parametrize("gap_fraction", [0.05, 0.10, 0.15])
def test_gap_fraction_tolerance_clustered(gap_fraction: float):
    """
    Test that generated clustered masks match the target gap fraction within ±0.5%.
    
    Clustered masks may have slightly higher variance due to the clustering
    algorithm, so we use a slightly more lenient check if needed, but the
    requirement is still ±0.5%.
    """
    nside = 512
    target_fraction = gap_fraction
    tolerance = 0.005  # ±0.5%
    
    # Generate mask with fixed seed for reproducibility
    mask = generate_clustered_mask(nside, target_fraction, seed=42, cluster_size=10)
    
    actual_fraction = _calculate_gap_fraction(mask)
    deviation = abs(actual_fraction - target_fraction)
    
    assert deviation <= tolerance, (
        f"Clustered mask gap fraction deviation too large: "
        f"target={target_fraction:.4f}, actual={actual_fraction:.4f}, "
        f"deviation={deviation:.4f}, tolerance={tolerance}"
    )


def test_gap_fraction_tolerance_edge_cases():
    """
    Test edge cases for gap fraction tolerance.
    
    Verifies behavior for very small and very large gap fractions.
    """
    nside = 512
    tolerance = 0.005  # ±0.5%
    
    # Test very small gap fraction
    target_small = 0.01
    mask_small = generate_random_mask(nside, target_small, seed=123)
    actual_small = _calculate_gap_fraction(mask_small)
    assert abs(actual_small - target_small) <= tolerance, (
        f"Small gap fraction failed: target={target_small}, actual={actual_small}"
    )
    
    # Test very large gap fraction
    target_large = 0.50
    mask_large = generate_random_mask(nside, target_large, seed=456)
    actual_large = _calculate_gap_fraction(mask_large)
    assert abs(actual_large - target_large) <= tolerance, (
        f"Large gap fraction failed: target={target_large}, actual={actual_large}"
    )


def test_mask_deterministic_with_seed():
    """
    Verify that mask generation is deterministic when using the same seed.
    """
    nside = 512
    gap_fraction = 0.10
    seed = 999
    
    mask1 = generate_random_mask(nside, gap_fraction, seed=seed)
    mask2 = generate_random_mask(nside, gap_fraction, seed=seed)
    
    assert np.array_equal(mask1, mask2), "Mask generation is not deterministic with same seed"


def test_mask_boolean_type():
    """
    Verify that generated masks are boolean arrays.
    """
    nside = 512
    gap_fraction = 0.10
    
    mask = generate_random_mask(nside, gap_fraction, seed=42)
    
    assert mask.dtype == bool, f"Mask should be boolean, got {mask.dtype}"