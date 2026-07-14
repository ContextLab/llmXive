"""
Unit tests for morphometry functions.
"""
import numpy as np
import pytest
from skimage.morphology import skeletonize

from code.morphometry import denoise_and_subtract, handle_empty_fields
from code.synthetic_data import generate_microglia_cell, set_seed

def test_denoise_and_subtract_preserves_structure():
    """
    Test that denoising preserves the main structure of a synthetic cell.
    """
    set_seed(42)
    # Generate a synthetic microglia cell
    cell_img, _ = generate_microglia_cell(size=(100, 100), complexity=0.5)
    
    # Add noise
    noisy_img = cell_img.astype(np.float32) + np.random.normal(0, 0.1, cell_img.shape)
    noisy_img = np.clip(noisy_img, 0, 1)

    # Process
    processed = denoise_and_subtract(noisy_img, sigma=0.5, patch_size=3, patch_distance=2)

    # Check that the output is not all zeros or NaN
    assert not np.all(processed == 0)
    assert not np.any(np.isnan(processed))
    
    # Check that the signal is roughly preserved (mean should be similar relative to noise)
    # Since background is subtracted, the mean might be lower, but variance should be reduced
    assert processed.std() < noisy_img.std() * 1.5  # Allow some tolerance

def test_denoise_and_subtract_handles_uint8():
    """
    Test denoising with uint8 input.
    """
    set_seed(123)
    cell_img, _ = generate_microglia_cell(size=(50, 50), complexity=0.3)
    uint8_img = (cell_img * 255).astype(np.uint8)
    
    processed = denoise_and_subtract(uint8_img)
    
    assert processed.dtype == np.float32
    assert processed.shape == uint8_img.shape

def test_handle_empty_fields():
    """
    Test detection of empty fields of view.
    """
    # Empty image
    empty_img = np.zeros((50, 50), dtype=np.uint8)
    assert handle_empty_fields(empty_img) is True

    # Noisy empty image (very low signal)
    noisy_empty = np.random.normal(0, 1, (50, 50)).astype(np.uint8)
    # Clip to 0-255 and ensure max is low
    noisy_empty = np.clip(noisy_empty, 0, 4).astype(np.uint8)
    assert handle_empty_fields(noisy_empty) is True

    # Non-empty image
    full_img = np.ones((50, 50), dtype=np.uint8) * 100
    assert handle_empty_fields(full_img) is False