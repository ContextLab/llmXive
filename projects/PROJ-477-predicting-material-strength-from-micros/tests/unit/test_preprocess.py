"""Unit tests for image resizing and normalization in the preprocessing pipeline.

These tests verify that the image processing functions in `code/data/preprocess.py`
correctly resize images to target dimensions, normalize pixel values to [0, 1],
and handle corrupted or invalid image inputs by raising appropriate errors.
"""

import os
import sys
import tempfile
import pytest
import numpy as np
from pathlib import Path

# Add the code directory to the path to allow imports from sibling modules
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from data.preprocess import resize_with_aspect_ratio, normalize_image, preprocess_single_image


class TestResizeNormalization:
    """Tests for image resizing and normalization logic."""

    def test_resize_normalizes_correctly_rgb(self):
        """Test that RGB images are resized correctly and normalized to [0, 1]."""
        # Create a synthetic RGB image with known values
        input_shape = (100, 100, 3)
        target_shape = (50, 50)  # (height, width)
        input_image = np.random.randint(0, 256, size=input_shape, dtype=np.uint8)

        # Resize
        resized = resize_with_aspect_ratio(input_image, target_shape)

        # Check shape
        assert resized.shape[0] == target_shape[0], f"Expected height {target_shape[0]}, got {resized.shape[0]}"
        assert resized.shape[1] == target_shape[1], f"Expected width {target_shape[1]}, got {resized.shape[1]}"
        assert resized.shape[2] == 3, "Expected 3 channels"

        # Normalize
        normalized = normalize_image(resized)

        # Check normalization range
        assert normalized.min() >= 0.0, "Normalized values should be >= 0"
        assert normalized.max() <= 1.0, "Normalized values should be <= 1"
        assert normalized.dtype == np.float32, "Normalized image should be float32"

    def test_resize_normalizes_correctly_grayscale(self):
        """Test that grayscale images are resized correctly and normalized to [0, 1]."""
        # Create a synthetic grayscale image
        input_shape = (80, 80)
        target_shape = (40, 40)
        input_image = np.random.randint(0, 256, size=input_shape, dtype=np.uint8)

        # Resize
        resized = resize_with_aspect_ratio(input_image, target_shape)

        # Check shape
        assert resized.shape == target_shape, f"Expected shape {target_shape}, got {resized.shape}"

        # Normalize
        normalized = normalize_image(resized)

        # Check normalization range
        assert normalized.min() >= 0.0, "Normalized values should be >= 0"
        assert normalized.max() <= 1.0, "Normalized values should be <= 1"
        assert normalized.dtype == np.float32, "Normalized image should be float32"

    def test_resize_preserves_aspect_ratio(self):
        """Test that aspect ratio is preserved during resize with padding."""
        # Create a non-square image
        input_shape = (200, 100, 3)  # 2:1 aspect ratio
        target_shape = (100, 100)
        input_image = np.random.randint(0, 256, size=input_shape, dtype=np.uint8)

        resized = resize_with_aspect_ratio(input_image, target_shape)

        # The resized image should fit within the target dimensions
        assert resized.shape[0] <= target_shape[0]
        assert resized.shape[1] <= target_shape[1]

        # Check that at least one dimension matches the target (no unnecessary padding)
        assert resized.shape[0] == target_shape[0] or resized.shape[1] == target_shape[1]

    def test_normalize_with_extreme_values(self):
        """Test normalization with images containing 0 and 255 values."""
        input_shape = (50, 50, 3)
        input_image = np.zeros(input_shape, dtype=np.uint8)
        input_image[0, 0, 0] = 255  # Set one pixel to max

        resized = resize_with_aspect_ratio(input_image, (50, 50))
        normalized = normalize_image(resized)

        # Min should be 0.0, max should be 1.0
        assert normalized.min() == 0.0, "Min should be 0.0"
        assert normalized.max() == 1.0, "Max should be 1.0"


class TestCorruptedImageHandling:
    """Tests for handling of corrupted or invalid image inputs."""

    def test_corrupted_image_raises_value_error(self):
        """Test that a corrupted image (invalid bit depth) raises ValueError."""
        # Create a corrupted image with invalid bit depth (e.g., 16-bit where 8-bit expected)
        # Simulate a corrupted file by creating an array with invalid dtype for the function
        input_shape = (100, 100, 3)
        # Using int64 which is not a standard image dtype for this pipeline
        corrupted_image = np.random.randint(0, 2**32, size=input_shape, dtype=np.int64)

        with pytest.raises(ValueError, match="Invalid image dtype"):
            resize_with_aspect_ratio(corrupted_image, (50, 50))

    def test_nan_values_raise_error(self):
        """Test that images with NaN values raise ValueError."""
        input_shape = (100, 100, 3)
        input_image = np.random.rand(*input_shape).astype(np.float32)
        input_image[0, 0, 0] = np.nan

        with pytest.raises(ValueError, match="Image contains NaN or Inf values"):
            normalize_image(input_image)

    def test_empty_image_raises_error(self):
        """Test that an empty image raises ValueError."""
        input_image = np.zeros((0, 0, 3), dtype=np.uint8)

        with pytest.raises(ValueError, match="Image dimensions must be positive"):
            resize_with_aspect_ratio(input_image, (50, 50))

    def test_invalid_target_shape_raises_error(self):
        """Test that an invalid target shape raises ValueError."""
        input_shape = (100, 100, 3)
        input_image = np.random.randint(0, 256, size=input_shape, dtype=np.uint8)

        with pytest.raises(ValueError, match="Target shape dimensions must be positive"):
            resize_with_aspect_ratio(input_image, (0, 50))

    def test_extreme_aspect_ratio_handled(self):
        """Test that extreme aspect ratios are handled gracefully (with padding)."""
        # Very wide image
        input_shape = (50, 500, 3)
        target_shape = (100, 100)
        input_image = np.random.randint(0, 256, size=input_shape, dtype=np.uint8)

        # This should not raise an error, but may produce a small resized image with padding
        resized = resize_with_aspect_ratio(input_image, target_shape)

        assert resized.shape[0] <= target_shape[0]
        assert resized.shape[1] <= target_shape[1]
        assert resized.shape[2] == 3


class TestPreprocessSingleImage:
    """Tests for the full preprocessing pipeline on a single image."""

    def test_preprocess_single_image_complete_flow(self):
        """Test the complete preprocessing flow on a valid image."""
        input_shape = (128, 128, 3)
        input_image = np.random.randint(0, 256, size=input_shape, dtype=np.uint8)
        target_shape = (64, 64)

        # Preprocess
        processed = preprocess_single_image(input_image, target_shape)

        # Check final shape
        assert processed.shape == (target_shape[0], target_shape[1], 3), \
            f"Expected shape {target_shape[0], target_shape[1], 3}, got {processed.shape}"

        # Check normalization
        assert processed.min() >= 0.0
        assert processed.max() <= 1.0
        assert processed.dtype == np.float32

    def test_preprocess_single_image_grayscale(self):
        """Test preprocessing on a grayscale image."""
        input_shape = (128, 128)
        input_image = np.random.randint(0, 256, size=input_shape, dtype=np.uint8)
        target_shape = (64, 64)

        processed = preprocess_single_image(input_image, target_shape)

        # Grayscale should remain 2D
        assert processed.shape == target_shape
        assert processed.min() >= 0.0
        assert processed.max() <= 1.0
        assert processed.dtype == np.float32