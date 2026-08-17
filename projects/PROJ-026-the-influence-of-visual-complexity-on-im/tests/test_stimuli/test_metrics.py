import pytest
import numpy as np
import cv2
import os
from pathlib import Path

from code.stimuli.metrics import (
    calculate_edge_density, 
    calculate_entropy, 
    calculate_fractal_dim,
    process_image_vectorized
)

@pytest.fixture
def solid_color_image():
    """Create a solid color image (low complexity)."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:] = [128, 128, 128]
    return img

@pytest.fixture
def noise_image():
    """Create a random noise image (high complexity)."""
    return np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)

@pytest.fixture
def edge_image():
    """Create an image with clear edges."""
    img = np.zeros((100, 100), dtype=np.uint8)
    img[40:60, :] = 255
    return img

def test_edge_density_solid_color(solid_color_image):
    """Edge density should be near zero for solid color."""
    density = calculate_edge_density(solid_color_image)
    assert density < 0.01, f"Edge density for solid color should be near 0, got {density}"

def test_edge_density_noise(noise_image):
    """Edge density should be higher for noise than solid color."""
    density_noise = calculate_edge_density(noise_image)
    density_solid = calculate_edge_density(np.zeros((100, 100, 3), dtype=np.uint8))
    assert density_noise > density_solid, "Noise should have higher edge density"

def test_entropy_solid_color(solid_color_image):
    """Entropy should be near zero for solid color."""
    entropy_val = calculate_entropy(solid_color_image)
    assert entropy_val < 0.1, f"Entropy for solid color should be near 0, got {entropy_val}"

def test_entropy_noise(noise_image):
    """Entropy should be higher for noise."""
    entropy_noise = calculate_entropy(noise_image)
    entropy_solid = calculate_entropy(np.zeros((100, 100, 3), dtype=np.uint8))
    assert entropy_noise > entropy_solid, "Noise should have higher entropy"

def test_fractal_dim_solid_color(solid_color_image):
    """Fractal dimension should be low for solid color."""
    fd = calculate_fractal_dim(solid_color_image)
    # Fractal dimension for a 2D image should be between 1.0 (line) and 2.0 (plane)
    assert fd >= 1.0 and fd <= 2.0, f"Fractal dimension out of bounds: {fd}"
    # Solid color is very smooth, so FD should be close to 1.0
    assert fd < 1.5, f"Fractal dimension for solid color should be low, got {fd}"

def test_fractal_dim_noise(noise_image):
    """Fractal dimension should be higher for noise."""
    fd_noise = calculate_fractal_dim(noise_image)
    fd_solid = calculate_fractal_dim(np.zeros((100, 100, 3), dtype=np.uint8))
    assert fd_noise > fd_solid, "Noise should have higher fractal dimension"

def test_process_image_vectorized(solid_color_image):
    """Test the vectorized wrapper returns correct tuple."""
    edge_d, ent, fd = process_image_vectorized(solid_color_image)
    assert isinstance(edge_d, float)
    assert isinstance(ent, float)
    assert isinstance(fd, float)
    assert edge_d >= 0 and edge_d <= 1
    assert ent >= 0
    assert fd >= 1.0 and fd <= 2.0

def test_edge_image_detection(edge_image):
    """Test that an image with clear edges is detected."""
    # Convert to BGR for consistency with function expectations
    edge_image_bgr = cv2.cvtColor(edge_image, cv2.COLOR_GRAY2BGR)
    density = calculate_edge_density(edge_image_bgr)
    assert density > 0.05, f"Edge image should have detectable edges, got {density}"