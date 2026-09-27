"""
Unit tests for code/utils/feature_extraction.py
Verifies lesion area ratio, color index, and entropy calculations.
"""
import pytest
import numpy as np
import cv2
from pathlib import Path

# Import the specific functions to test
from utils.feature_extraction import extract_lesion_area_ratio, extract_necrosis_color_index, extract_texture_entropy

def test_extract_lesion_area_ratio_simple(tmp_path, sample_image_path):
    """Test lesion area ratio on a synthetic image with a known 'lesion'."""
    # Create an image with a distinct black center (simulating necrosis/lesion)
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    # Draw a black square in the center (20x20 = 400 pixels)
    center = 50
    half = 10
    img[center-half:center+half, center-half:center+half] = [0, 0, 0]
    
    # Save temporarily if needed, but function takes path
    temp_path = tmp_path / "lesion_test.png"
    cv2.imwrite(str(temp_path), img)
    
    ratio = extract_lesion_area_ratio(str(temp_path))
    
    # Total pixels = 10000, Lesion pixels approx 400 (depends on threshold logic)
    # The function typically thresholds low intensity.
    assert 0.0 <= ratio <= 1.0
    # Expect a non-zero ratio since we added a black square
    assert ratio > 0.0

def test_extract_necrosis_color_index_uniform():
    """Test color index on a uniform green image (healthy)."""
    # Create a uniform green image
    img = np.ones((50, 50, 3), dtype=np.uint8) * 0  # Black base
    img[:, :] = [0, 150, 0] # Pure Green
    
    # We need a file path for the function
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        cv2.imwrite(f.name, img)
        path = f.name
    
    try:
        # Healthy green should have low necrosis index (brown/black)
        index = extract_necrosis_color_index(path)
        assert isinstance(index, float)
        assert index >= 0.0
    finally:
        os.unlink(path)

def test_extract_texture_entropy_constant():
    """Test entropy on a constant image (should be 0 or very low)."""
    img = np.ones((30, 30, 3), dtype=np.uint8) * 128
    
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        cv2.imwrite(f.name, img)
        path = f.name
    
    try:
        entropy = extract_texture_entropy(path)
        assert isinstance(entropy, float)
        # A constant image has very low entropy
        assert entropy < 1.0 # Threshold is arbitrary but should be low
    finally:
        os.unlink(path)
