"""
Unit tests for image resizing and normalization in code/data/preprocess.py.

These tests verify:
1. Images are resized to the target dimensions (224x224) while maintaining aspect ratio logic.
2. Pixel values are normalized to the expected range (0-1 or [-1, 1] depending on config).
3. Edge cases (small images, large images, grayscale) are handled correctly.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import cv2

# Add the project root to the path to allow imports from code/
# Assuming this test runs from the project root or the tests directory
project_root = Path(__file__).parent.parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from data.preprocess import resize_with_aspect_ratio, normalize_image, preprocess_single_image
from utils.config import get_project_root


class TestResizeWithAspectRatio(unittest.TestCase):
    """Tests for the resize_with_aspect_ratio function."""

    def setUp(self):
        """Create temporary test images."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_image(self, filename, shape, dtype=np.uint8):
        """Helper to create a dummy image file."""
        # shape is (H, W, C) or (H, W)
        img = np.random.randint(0, 255, shape, dtype=dtype)
        path = os.path.join(self.temp_dir, filename)
        cv2.imwrite(path, img)
        return path

    def test_resize_larger_image(self):
        """Test resizing an image larger than target (300x300 -> 224x224)."""
        img_path = self._create_test_image("large.png", (300, 300, 3))
        target_size = (224, 224)

        resized_img = resize_with_aspect_ratio(img_path, target_size)

        self.assertIsNotNone(resized_img)
        self.assertEqual(resized_img.shape[0], target_size[0])
        self.assertEqual(resized_img.shape[1], target_size[1])
        # Check that it's a numpy array
        self.assertIsInstance(resized_img, np.ndarray)

    def test_resize_smaller_image(self):
        """Test resizing an image smaller than target (100x100 -> 224x224)."""
        img_path = self._create_test_image("small.png", (100, 100, 3))
        target_size = (224, 224)

        resized_img = resize_with_aspect_ratio(img_path, target_size)

        self.assertIsNotNone(resized_img)
        self.assertEqual(resized_img.shape[0], target_size[0])
        self.assertEqual(resized_img.shape[1], target_size[1])

    def test_resize_non_square_preserves_aspect_ratio_logic(self):
        """Test that aspect ratio is respected (padding logic if implemented, or simple stretch check)."""
        # Create a 400x200 image (2:1 aspect ratio)
        img_path = self._create_test_image("rect.png", (200, 400, 3))
        target_size = (224, 224)

        resized_img = resize_with_aspect_ratio(img_path, target_size)

        # The function is expected to resize to the target size.
        # If the implementation uses padding to maintain aspect ratio,
        # the output should be 224x224 with black bars.
        # If it stretches, it is 224x224.
        # In either case, dimensions must match target.
        self.assertEqual(resized_img.shape[0], target_size[0])
        self.assertEqual(resized_img.shape[1], target_size[1])

    def test_grayscale_image(self):
        """Test resizing a grayscale image."""
        img_path = self._create_test_image("gray.png", (150, 150)) # No channel dim
        target_size = (224, 224)

        resized_img = resize_with_aspect_ratio(img_path, target_size)

        self.assertIsNotNone(resized_img)
        self.assertEqual(resized_img.shape[0], target_size[0])
        self.assertEqual(resized_img.shape[1], target_size[1])
        # Grayscale might remain 2D or become 3D with 1 channel depending on cv2.INTER_
        # We just check dimensions match target.


class TestNormalizeImage(unittest.TestCase):
    """Tests for the normalize_image function."""

    def test_normalize_uint8_to_float(self):
        """Test converting uint8 (0-255) to float (0.0-1.0)."""
        # Create a test array
        img = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
        normalized = normalize_image(img)

        self.assertEqual(normalized.dtype, np.float32)
        self.assertTrue(np.all(normalized >= 0.0))
        self.assertTrue(np.all(normalized <= 1.0))

    def test_normalize_specific_values(self):
        """Test normalization with known values."""
        img = np.array([[[0, 128, 255]]], dtype=np.uint8)
        normalized = normalize_image(img)

        # 0 -> 0.0, 128 -> 0.50196..., 255 -> 1.0
        expected_min = 0.0
        expected_max = 1.0
        expected_mid = 128.0 / 255.0

        self.assertAlmostEqual(normalized[0, 0, 0], expected_min, places=5)
        self.assertAlmostEqual(normalized[0, 0, 1], expected_mid, places=5)
        self.assertAlmostEqual(normalized[0, 0, 2], expected_max, places=5)

    def test_normalize_preserves_shape(self):
        """Test that normalization does not change image shape."""
        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        normalized = normalize_image(img)

        self.assertEqual(img.shape, normalized.shape)


class TestPreprocessSingleImage(unittest.TestCase):
    """Tests for the full preprocessing pipeline on a single image."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_image(self, filename, shape):
        img = np.random.randint(0, 255, shape, dtype=np.uint8)
        path = os.path.join(self.temp_dir, filename)
        cv2.imwrite(path, img)
        return path

    def test_full_pipeline_output_dimensions(self):
        """Test that the full pipeline produces a 224x224 normalized image."""
        img_path = self._create_test_image("test.png", (300, 300, 3))
        target_size = (224, 224)

        result = preprocess_single_image(img_path, target_size)

        # result is typically a numpy array (H, W, C) float32
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.shape[0], target_size[0])
        self.assertEqual(result.shape[1], target_size[1])
        self.assertEqual(result.dtype, np.float32)
        self.assertTrue(np.all(result >= 0.0))
        self.assertTrue(np.all(result <= 1.0))

    def test_full_pipeline_grayscale(self):
        """Test full pipeline on a grayscale image."""
        img_path = self._create_test_image("gray.png", (100, 100))
        target_size = (224, 224)

        result = preprocess_single_image(img_path, target_size)

        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(result.shape[0], target_size[0])
        self.assertEqual(result.shape[1], target_size[1])
        # Grayscale might result in shape (224, 224, 1) or (224, 224)
        # Check that spatial dimensions are correct.
        self.assertEqual(result.shape[0], 224)
        self.assertEqual(result.shape[1], 224)


if __name__ == '__main__':
    unittest.main()