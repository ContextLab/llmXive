import pytest
import numpy as np
import cv2
from pathlib import Path
import tempfile
import os

from code.analysis.feature_gen import (
    compute_luminance,
    compute_contrast,
    compute_edge_density,
    process_image_features,
    collect_image_paths
)

def test_compute_luminance_uniform_image():
    """Test luminance calculation on a uniform grayscale image."""
    # Create a 10x10 image with all pixels set to 128
    image = np.full((10, 10, 3), 128, dtype=np.uint8)
    luminance = compute_luminance(image)
    assert abs(luminance - 128.0) < 0.001

def test_compute_contrast_uniform_image():
    """Test contrast calculation on a uniform image (should be 0)."""
    image = np.full((10, 10, 3), 128, dtype=np.uint8)
    contrast = compute_contrast(image)
    assert contrast == 0.0

def test_compute_contrast_gradient_image():
    """Test contrast calculation on a gradient image."""
    # Create a gradient image
    gradient = np.linspace(0, 255, 100).reshape(10, 10).astype(np.uint8)
    image = np.stack([gradient, gradient, gradient], axis=2)
    contrast = compute_contrast(image)
    # The standard deviation of a uniform gradient from 0 to 255 is approx 73.9
    assert 70 < contrast < 78

def test_compute_edge_density_no_edges():
    """Test edge density on a uniform image (should be 0)."""
    image = np.full((50, 50, 3), 128, dtype=np.uint8)
    edge_density = compute_edge_density(image)
    assert edge_density == 0.0

def test_compute_edge_density_strong_edges():
    """Test edge density on an image with a strong vertical edge."""
    image = np.zeros((50, 50, 3), dtype=np.uint8)
    image[:, 25:] = 255  # Create a sharp vertical edge
    edge_density = compute_edge_density(image)
    # There should be some edges detected around the transition
    assert edge_density > 0.0
    assert edge_density <= 1.0

def test_process_image_features(tmp_path):
    """Test full processing of a single image."""
    # Create a test image
    test_image = np.zeros((100, 100, 3), dtype=np.uint8)
    test_image[:, 50:] = 255  # Vertical edge
    
    image_path = tmp_path / "test_image.png"
    cv2.imwrite(str(image_path), test_image)
    
    image_id, luminance, contrast, edge_density = process_image_features(image_path)
    
    assert image_id == "test_image"
    assert isinstance(luminance, float)
    assert isinstance(contrast, float)
    assert isinstance(edge_density, float)
    assert edge_density > 0.0  # Should detect the edge

def test_process_image_features_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        process_image_features(Path("/nonexistent/path/image.png"))

def test_collect_image_paths(tmp_path):
    """Test collection of image paths from a directory."""
    # Create test files
    (tmp_path / "img1.jpg").touch()
    (tmp_path / "img2.png").touch()
    (tmp_path / "readme.txt").touch()
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "img3.jpeg").touch()
    
    image_paths = collect_image_paths(tmp_path)
    
    # Should find 3 images (jpg, png, jpeg)
    assert len(image_paths) == 3
    
    # Verify extensions
    extensions = [p.suffix.lower() for p in image_paths]
    assert set(extensions) == {'.jpg', '.png', '.jpeg'}

def test_collect_image_paths_empty_dir(tmp_path):
    """Test collection from an empty directory."""
    image_paths = collect_image_paths(tmp_path)
    assert len(image_paths) == 0
