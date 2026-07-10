"""
Unit tests for stimulus complexity metrics.
"""
import os
import tempfile
import numpy as np
import pytest
from PIL import Image
import cv2

# Import the functions being tested
from code.stimuli.metrics import (
    calculate_edge_density,
    calculate_entropy,
    calculate_fractal_dim
)


def create_test_image(size=(128, 128), mode="solid", noise_level=0.0):
    """
    Helper to create test images.
    
    Args:
        size: (width, height)
        mode: "solid", "noise", "gradient", "checkerboard"
        noise_level: 0.0 to 1.0 (for noise mode)
    
    Returns:
        Path to a temporary PNG file.
    """
    img_array = np.zeros((size[1], size[0]), dtype=np.uint8)
    
    if mode == "solid":
        img_array[:, :] = 128
    elif mode == "noise":
        # Generate random noise
        noise = np.random.randint(0, 256, size=(size[1], size[0]), dtype=np.uint8)
        img_array = noise
    elif mode == "gradient":
        for x in range(size[0]):
            img_array[:, x] = int(255 * x / (size[0] - 1))
    elif mode == "checkerboard":
        block_size = 8
        for y in range(size[1]):
            for x in range(size[0]):
                if (x // block_size + y // block_size) % 2 == 0:
                    img_array[y, x] = 255
                else:
                    img_array[y, x] = 0
    
    # Save to temp file
    temp_fd, temp_path = tempfile.mkstemp(suffix=".png")
    os.close(temp_fd)
    cv2.imwrite(temp_path, img_array)
    return temp_path


class TestEdgeDensity:
    def test_solid_image_low_density(self):
        """Solid image should have very low edge density."""
        path = create_test_image(mode="solid")
        try:
            density = calculate_edge_density(path)
            # Solid image has no edges, density should be near 0
            assert 0 <= density < 0.01, f"Expected near 0, got {density}"
        finally:
            os.remove(path)

    def test_checkerboard_high_density(self):
        """Checkerboard should have higher edge density than solid."""
        solid_path = create_test_image(mode="solid")
        checker_path = create_test_image(mode="checkerboard")
        try:
            solid_density = calculate_edge_density(solid_path)
            checker_density = calculate_edge_density(checker_path)
            assert checker_density > solid_density, \
                f"Checkerboard ({checker_density}) should be > solid ({solid_density})"
        finally:
            os.remove(solid_path)
            os.remove(checker_path)


class TestEntropy:
    def test_solid_image_zero_entropy(self):
        """Solid image should have near-zero entropy."""
        path = create_test_image(mode="solid")
        try:
            ent = calculate_entropy(path)
            # All pixels same value -> entropy ~ 0
            assert ent < 0.1, f"Expected near 0, got {ent}"
        finally:
            os.remove(path)

    def test_noise_image_high_entropy(self):
        """Random noise should have high entropy."""
        solid_path = create_test_image(mode="solid")
        noise_path = create_test_image(mode="noise")
        try:
            solid_ent = calculate_entropy(solid_path)
            noise_ent = calculate_entropy(noise_path)
            assert noise_ent > solid_ent, \
                f"Noise ({noise_ent}) should be > solid ({solid_ent})"
            # Noise entropy should be reasonably high (max ~8 for 256 levels)
            assert noise_ent > 3.0, f"Expected high entropy for noise, got {noise_ent}"
        finally:
            os.remove(solid_path)
            os.remove(noise_path)


class TestFractalDimension:
    def test_solid_image_low_fractal_dim(self):
        """Solid image should have low fractal dimension (close to 2)."""
        path = create_test_image(mode="solid")
        try:
            dim = calculate_fractal_dim(path)
            # Solid image is flat, fractal dim should be near 2 (2D plane)
            assert 2.0 <= dim <= 2.2, f"Expected ~2.0, got {dim}"
        finally:
            os.remove(path)

    def test_noise_image_higher_fractal_dim(self):
        """Noise image should have higher fractal dimension than solid."""
        solid_path = create_test_image(mode="solid")
        noise_path = create_test_image(mode="noise")
        try:
            solid_dim = calculate_fractal_dim(solid_path)
            noise_dim = calculate_fractal_dim(noise_path)
            assert noise_dim > solid_dim, \
                f"Noise ({noise_dim}) should have higher fractal dim than solid ({solid_dim})"
        finally:
            os.remove(solid_path)
            os.remove(noise_path)

    def test_fractal_dim_bounded(self):
        """Fractal dimension should be within theoretical bounds for 2D images."""
        path = create_test_image(mode="noise")
        try:
            dim = calculate_fractal_dim(path)
            # For a 2D image, fractal dimension should be between 2 and 3
            assert 2.0 <= dim <= 3.0, f"Fractal dim {dim} out of bounds [2, 3]"
        finally:
            os.remove(path)

    def test_fractal_dim_consistency(self):
        """Same image processed twice should yield same fractal dimension."""
        path = create_test_image(mode="checkerboard")
        try:
            dim1 = calculate_fractal_dim(path)
            dim2 = calculate_fractal_dim(path)
            assert np.isclose(dim1, dim2), \
                f"Non-deterministic result: {dim1} vs {dim2}"
        finally:
            os.remove(path)

    def test_fractal_dim_on_gradient(self):
        """Gradient image should have intermediate fractal dimension."""
        solid_path = create_test_image(mode="solid")
        grad_path = create_test_image(mode="gradient")
        try:
            solid_dim = calculate_fractal_dim(solid_path)
            grad_dim = calculate_fractal_dim(grad_path)
            # Gradient is more complex than solid but less than noise
            assert grad_dim >= solid_dim, \
                f"Gradient ({grad_dim}) should be >= solid ({solid_dim})"
        finally:
            os.remove(solid_path)
            os.remove(grad_path)