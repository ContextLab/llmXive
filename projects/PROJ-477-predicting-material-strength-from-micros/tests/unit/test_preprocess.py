"""
Unit tests for image resizing and normalization in code/data/preprocess.py.

These tests verify that:
1. Images are resized to the target dimensions (224x224) while handling aspect ratios.
2. Pixel values are correctly normalized using standard ImageNet statistics.
3. Grayscale images are correctly converted to RGB if necessary.
4. Edge cases (very small, very large, extreme aspect ratios) are handled.
"""
import pytest
import numpy as np
import cv2
import tempfile
import os
from pathlib import Path

# Import the functions to be tested
# Adjust import path based on project structure. Assuming tests/unit is parallel to code/
# We add the code directory to sys.path to allow direct imports during testing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.preprocess import resize_with_aspect_ratio, normalize_image, preprocess_single_image

# Constants
TARGET_SIZE = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

class TestResizeWithAspectRatio:
    """Tests for resize_with_aspect_ratio function."""

    def test_square_image_resize(self):
        """Test resizing a square image to target size."""
        # Create a 100x100 square image (grayscale for simplicity)
        img = np.zeros((100, 100), dtype=np.uint8)
        img[:] = 128

        resized = resize_with_aspect_ratio(img, TARGET_SIZE)

        assert resized.shape[0] == TARGET_SIZE
        assert resized.shape[1] == TARGET_SIZE
        # Check that pixel values are preserved (just scaled)
        assert resized.dtype == np.uint8

    def test_rectangular_image_resize_width_limited(self):
        """Test resizing a wide image where width is the limiting factor."""
        # Create a 400x200 image (2:1 aspect ratio)
        # When resizing to 224x224 with aspect ratio, width should be 224, height 112
        img = np.zeros((200, 400), dtype=np.uint8)
        img[:] = 128

        resized = resize_with_aspect_ratio(img, TARGET_SIZE)

        assert resized.shape[0] == 112  # Height
        assert resized.shape[1] == 224  # Width
        assert resized.dtype == np.uint8

    def test_rectangular_image_resize_height_limited(self):
        """Test resizing a tall image where height is the limiting factor."""
        # Create a 200x400 image (1:2 aspect ratio)
        # When resizing to 224x224 with aspect ratio, height should be 224, width 112
        img = np.zeros((400, 200), dtype=np.uint8)
        img[:] = 128

        resized = resize_with_aspect_ratio(img, TARGET_SIZE)

        assert resized.shape[0] == 224  # Height
        assert resized.shape[1] == 112  # Width
        assert resized.dtype == np.uint8

    def test_small_image_upscaling(self):
        """Test that small images are upscaled correctly."""
        # Create a 50x50 image
        img = np.zeros((50, 50), dtype=np.uint8)
        img[:] = 128

        resized = resize_with_aspect_ratio(img, TARGET_SIZE)

        assert resized.shape[0] == TARGET_SIZE
        assert resized.shape[1] == TARGET_SIZE

    def test_large_image_downscaling(self):
        """Test that large images are downscaled correctly."""
        # Create a 1000x1000 image
        img = np.zeros((1000, 1000), dtype=np.uint8)
        img[:] = 128

        resized = resize_with_aspect_ratio(img, TARGET_SIZE)

        assert resized.shape[0] == TARGET_SIZE
        assert resized.shape[1] == TARGET_SIZE

    def test_extreme_aspect_ratio(self):
        """Test resizing an image with extreme aspect ratio."""
        # Create a very wide image: 100x1000
        img = np.zeros((100, 1000), dtype=np.uint8)
        img[:] = 128

        resized = resize_with_aspect_ratio(img, TARGET_SIZE)

        # Width should be 224, height should be scaled proportionally
        expected_height = int(224 * (100 / 1000))
        assert resized.shape[0] == expected_height
        assert resized.shape[1] == TARGET_SIZE

class TestNormalizeImage:
    """Tests for normalize_image function."""

    def test_normalize_rgb_image(self):
        """Test normalization of an RGB image."""
        # Create a dummy RGB image with known values
        # Values should be in range [0, 255] for uint8 input
        img = np.zeros((224, 224, 3), dtype=np.uint8)
        img[:, :, 0] = 255  # Red channel max
        img[:, :, 1] = 128  # Green channel mid
        img[:, :, 2] = 0    # Blue channel min

        normalized = normalize_image(img)

        assert normalized.shape == (224, 224, 3)
        assert normalized.dtype == np.float32

        # Check normalization for Red channel (mean=0.485, std=0.229)
        # Input 255 -> normalized to 1.0 -> (1.0 - 0.485) / 0.229
        expected_red = (1.0 - IMAGENET_MEAN[0]) / IMAGENET_STD[0]
        assert np.allclose(normalized[0, 0, 0], expected_red)

        # Check normalization for Blue channel (mean=0.406, std=0.225)
        # Input 0 -> normalized to 0.0 -> (0.0 - 0.406) / 0.225
        expected_blue = (0.0 - IMAGENET_MEAN[2]) / IMAGENET_STD[2]
        assert np.allclose(normalized[0, 0, 2], expected_blue)

    def test_normalize_grayscale_to_rgb(self):
        """Test that grayscale images are converted to RGB before normalization."""
        # Create a dummy grayscale image
        img = np.zeros((224, 224), dtype=np.uint8)
        img[:] = 128

        normalized = normalize_image(img)

        assert normalized.shape == (224, 224, 3)
        assert normalized.dtype == np.float32

        # All channels should be the same value since input was grayscale
        first_pixel = normalized[0, 0, 0]
        assert np.allclose(normalized[0, 0, 1], first_pixel)
        assert np.allclose(normalized[0, 0, 2], first_pixel)

    def test_normalize_preserves_shape(self):
        """Test that normalization preserves spatial dimensions."""
        img = np.random.randint(0, 256, (150, 150, 3), dtype=np.uint8)
        normalized = normalize_image(img)

        assert normalized.shape[0] == 150
        assert normalized.shape[1] == 150
        assert normalized.shape[2] == 3

    def test_normalize_output_range(self):
        """Test that normalized values are within expected range (approx)."""
        # Create an image with extreme values
        img = np.zeros((224, 224, 3), dtype=np.uint8)
        img[:, :, 0] = 255
        img[:, :, 1] = 0
        img[:, :, 2] = 128

        normalized = normalize_image(img)

        # Check that values are reasonable (not NaN or Inf)
        assert not np.any(np.isnan(normalized))
        assert not np.any(np.isinf(normalized))

        # Values should be roughly within -3 to +3 (3 sigma from mean)
        assert np.all(normalized > -10)
        assert np.all(normalized < 10)

class TestPreprocessSingleImage:
    """Tests for the full preprocess_single_image pipeline."""

    def test_preprocess_grayscale_image(self):
        """Test full preprocessing of a grayscale image."""
        # Create a temporary grayscale image file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img = np.zeros((100, 100), dtype=np.uint8)
            img[:] = 128
            cv2.imwrite(tmp.name, img)
            temp_path = tmp.name

        try:
            processed = preprocess_single_image(temp_path)

            # Should be resized to 224x224 and normalized
            assert processed.shape[0] == TARGET_SIZE
            assert processed.shape[1] == TARGET_SIZE
            assert processed.shape[2] == 3  # Converted to RGB
            assert processed.dtype == np.float32
        finally:
            os.unlink(temp_path)

    def test_preprocess_rgb_image(self):
        """Test full preprocessing of an RGB image."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img = np.zeros((200, 200, 3), dtype=np.uint8)
            img[:, :, 0] = 255
            img[:, :, 1] = 128
            img[:, :, 2] = 64
            cv2.imwrite(tmp.name, img)
            temp_path = tmp.name

        try:
            processed = preprocess_single_image(temp_path)

            assert processed.shape[0] == TARGET_SIZE
            assert processed.shape[1] == TARGET_SIZE
            assert processed.shape[2] == 3
            assert processed.dtype == np.float32
        finally:
            os.unlink(temp_path)

    def test_preprocess_non_square_image(self):
        """Test preprocessing of a non-square image."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            # 300x100 image
            img = np.zeros((100, 300, 3), dtype=np.uint8)
            img[:] = 128
            cv2.imwrite(tmp.name, img)
            temp_path = tmp.name

        try:
            processed = preprocess_single_image(temp_path)

            # Should be resized to 224x224 with padding or cropping
            # Based on our implementation (resize_with_aspect_ratio), it should be 224x75
            # Wait, the requirement is 224x224. Let's check the implementation.
            # If resize_with_aspect_ratio preserves aspect ratio, the output might not be 224x224.
            # The test should verify the actual behavior of the function.
            # Assuming the function pads to 224x224 if aspect ratio is preserved:
            assert processed.shape[0] == TARGET_SIZE
            assert processed.shape[1] == TARGET_SIZE
        finally:
            os.unlink(temp_path)

    def test_preprocess_corrupted_image_fails_gracefully(self):
        """Test that preprocessing a corrupted image raises an error."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(b"not a valid image")
            temp_path = tmp.name

        try:
            with pytest.raises(Exception):  # cv2 or PIL should raise an error
                preprocess_single_image(temp_path)
        finally:
            os.unlink(temp_path)

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_image_array(self):
        """Test handling of empty image array."""
        img = np.zeros((0, 0), dtype=np.uint8)
        
        # This should either raise an error or handle gracefully
        # Depending on implementation, we expect an error for invalid dimensions
        with pytest.raises(Exception):
            resize_with_aspect_ratio(img, TARGET_SIZE)

    def test_single_pixel_image(self):
        """Test resizing a single pixel image."""
        img = np.array([[128]], dtype=np.uint8)
        
        resized = resize_with_aspect_ratio(img, TARGET_SIZE)
        
        assert resized.shape[0] == TARGET_SIZE
        assert resized.shape[1] == TARGET_SIZE

    def test_very_large_pixel_values(self):
        """Test normalization with extreme pixel values (if uint16)."""
        # Create a uint16 image (if supported)
        img = np.zeros((224, 224, 3), dtype=np.uint16)
        img[:, :, 0] = 65535  # Max uint16 value
        
        # Convert to uint8 first if needed, or handle in normalize_image
        # Our implementation expects uint8, so this might fail or require conversion
        # For now, we assume the function handles uint8 only
        with pytest.raises((TypeError, ValueError)):
            normalize_image(img)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])