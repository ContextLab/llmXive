"""
Unit test for mask generation tolerance.

Tests that generated mask pixel count matches target fraction ±0.5%.
"""
import os
import sys
import numpy as np
import pytest
from pathlib import Path

# Ensure code directory is in path
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from simulation.utils import generate_random_mask
from config import N_SIDE

def test_gap_fraction_tolerance():
    """
    Assert that generated mask pixel count matches target fraction ±0.5%.
    """
    target_fraction = 0.10
    tolerance = 0.005  # ±0.5%
    
    # Generate mask
    mask = generate_random_mask(N_SIDE, target_fraction)
    
    # Calculate actual gap fraction
    total_pixels = len(mask)
    masked_pixels = np.sum(mask == 0) # Assuming 0 is masked
    actual_fraction = masked_pixels / total_pixels
    
    # Assert within tolerance
    assert abs(actual_fraction - target_fraction) <= tolerance, \
        f"Actual gap fraction {actual_fraction} not within tolerance of {target_fraction} (±{tolerance})"
    
    print(f"Mask generation test passed: Target={target_fraction}, Actual={actual_fraction}")

if __name__ == "__main__":
    test_gap_fraction_tolerance()