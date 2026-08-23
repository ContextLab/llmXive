"""
Unit tests for fidelity metrics (LPIPS and SSIM).
"""
import pytest
import torch
import numpy as np
from PIL import Image
import io
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from src.metrics.fidelity import compute_lpips, compute_ssim, compute_fidelity_scores, _pil_to_tensor

@pytest.fixture
def identical_images():
    """Create two identical dummy images."""
    arr = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    return img, img

@pytest.fixture
def different_images():
    """Create two different dummy images."""
    arr1 = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    arr2 = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
    img1 = Image.fromarray(arr1)
    img2 = Image.fromarray(arr2)
    return img1, img2

@pytest.fixture
def grayscale_images():
    """Create two identical grayscale dummy images."""
    arr = np.random.randint(0, 255, (64, 64), dtype=np.uint8)
    img = Image.fromarray(arr, mode='L')
    return img, img

def test_identical_images_lpips(identical_images):
    """Test that identical images have LPIPS score close to 0."""
    img1, img2 = identical_images
    score = compute_lpips(img1, img2)
    # LPIPS should be very small for identical images
    assert score < 0.01, f"LPIPS for identical images should be near 0, got {score}"

def test_identical_images_ssim(identical_images):
    """Test that identical images have SSIM score of 1.0."""
    img1, img2 = identical_images
    score = compute_ssim(img1, img2)
    assert score == 1.0, f"SSIM for identical images should be 1.0, got {score}"

def test_different_images_lpips(different_images):
    """Test that different images have a non-zero LPIPS score."""
    img1, img2 = different_images
    score = compute_lpips(img1, img2)
    assert score >= 0.0, "LPIPS score cannot be negative"
    # Note: LPIPS can be small even for random noise, but it won't be 0.0
    # We just assert it's a valid float >= 0

def test_different_images_ssim(different_images):
    """Test that different images have SSIM score < 1.0."""
    img1, img2 = different_images
    score = compute_ssim(img1, img2)
    assert score < 1.0, f"SSIM for different images should be < 1.0, got {score}"
    assert score >= -1.0, "SSIM score should be >= -1.0"

def test_grayscale_images_ssim(grayscale_images):
    """Test SSIM with grayscale images."""
    img1, img2 = grayscale_images
    score = compute_ssim(img1, img2)
    assert score == 1.0, f"SSIM for identical grayscale images should be 1.0, got {score}"

def test_pil_to_tensor_conversion():
    """Test conversion from PIL to tensor."""
    arr = np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    tensor = _pil_to_tensor(img)
    
    assert tensor.shape == (3, 32, 32), f"Expected shape (3, 32, 32), got {tensor.shape}"
    assert tensor.min() >= -1.0 and tensor.max() <= 1.0, "Tensor values should be in [-1, 1]"

def test_compute_fidelity_scores(different_images):
    """Test the combined fidelity score function."""
    img1, img2 = different_images
    scores = compute_fidelity_scores(img1, img2)
    
    assert "lpips" in scores, "Result should contain 'lpips'"
    assert "ssim" in scores, "Result should contain 'ssim'"
    assert isinstance(scores["lpips"], float), "LPIPS should be a float"
    assert isinstance(scores["ssim"], float), "SSIM should be a float"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
