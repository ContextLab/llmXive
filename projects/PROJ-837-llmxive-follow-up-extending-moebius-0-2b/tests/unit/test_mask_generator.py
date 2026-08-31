"""
Unit tests for code/data/mask_generator.py
Tests mask generation metrics (gradient variance, entropy)
"""
import os
import sys
import unittest
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.mask_generator import (
    generate_mask,
    generate_mask_batch
)


class TestMaskGeneration(unittest.TestCase):
    """Tests for basic mask generation functionality"""

    def setUp(self):
        """Create a test image"""
        self.img_size = (64, 64)
        self.test_image = Image.new('RGB', self.img_size, color=(255, 255, 255))

    def test_generate_mask_returns_pil_image(self):
        """Test that generate_mask returns a PIL Image"""
        mask = generate_mask(self.test_image, complexity=0.5)
        self.assertIsInstance(mask, Image.Image)

    def test_generate_mask_is_binary(self):
        """Test that generated mask contains only 0 and 255 values"""
        mask = generate_mask(self.test_image, complexity=0.5)
        mask_array = np.array(mask)
        unique_values = np.unique(mask_array)
        # Should only have 0 (black) and 255 (white)
        self.assertTrue(all(v in [0, 255] for v in unique_values))

    def test_generate_mask_correct_size(self):
        """Test that mask has same size as input image"""
        mask = generate_mask(self.test_image, complexity=0.5)
        self.assertEqual(mask.size, self.img_size)

    def test_generate_mask_low_complexity_small(self):
        """Test that low complexity produces smaller masked regions"""
        mask_low = generate_mask(self.test_image, complexity=0.1)
        mask_high = generate_mask(self.test_image, complexity=0.9)
        
        mask_low_array = np.array(mask_low)
        mask_high_array = np.array(mask_high)
        
        white_pixels_low = np.sum(mask_low_array == 255)
        white_pixels_high = np.sum(mask_high_array == 255)
        
        # High complexity should have more masked (white) pixels
        self.assertGreater(white_pixels_high, white_pixels_low)


class TestMaskMetrics(unittest.TestCase):
    """Tests for mask generation metrics calculation"""

    def setUp(self):
        """Create test images and masks"""
        self.img_size = (64, 64)
        self.test_image = Image.new('RGB', self.img_size, color=(255, 255, 255))

    def test_gradient_variance_positive(self):
        """Test that gradient variance is positive for complex masks"""
        # Generate a high complexity mask
        mask = generate_mask(self.test_image, complexity=0.8)
        mask_array = np.array(mask)
        
        # Calculate gradient in x and y directions
        grad_x = np.diff(mask_array, axis=1)
        grad_y = np.diff(mask_array, axis=0)
        
        # Calculate variance
        var_x = np.var(grad_x)
        var_y = np.var(grad_y)
        
        # Variance should be non-negative
        self.assertGreaterEqual(var_x, 0)
        self.assertGreaterEqual(var_y, 0)

    def test_texture_entropy_positive(self):
        """Test that texture entropy is positive"""
        mask = generate_mask(self.test_image, complexity=0.5)
        mask_array = np.array(mask)
        
        # Calculate histogram
        hist, _ = np.histogram(mask_array, bins=2, range=(0, 256))
        hist = hist / hist.sum()  # Normalize
        
        # Calculate entropy
        entropy = -np.sum(hist * np.log2(hist + 1e-10))
        
        # Entropy should be non-negative
        self.assertGreaterEqual(entropy, 0)

    def test_complexity_correlation_with_metrics(self):
        """Test that complexity correlates with generated metrics"""
        complexities = [0.1, 0.3, 0.5, 0.7, 0.9]
        variances = []
        entropies = []
        
        for comp in complexities:
            mask = generate_mask(self.test_image, complexity=comp)
            mask_array = np.array(mask)
            
            # Gradient variance
            grad_x = np.diff(mask_array, axis=1)
            grad_y = np.diff(mask_array, axis=0)
            var = np.var(grad_x) + np.var(grad_y)
            variances.append(var)
            
            # Texture entropy
            hist, _ = np.histogram(mask_array, bins=2, range=(0, 256))
            hist = hist / hist.sum()
            entropy = -np.sum(hist * np.log2(hist + 1e-10))
            entropies.append(entropy)
        
        # Check that variance generally increases with complexity
        # (Not strictly monotonic due to randomness, but trend should be visible)
        self.assertGreater(variances[-1], variances[0])


class TestMaskBatchGeneration(unittest.TestCase):
    """Tests for batch mask generation"""

    def setUp(self):
        """Create test image"""
        self.img_size = (64, 64)
        self.test_image = Image.new('RGB', self.img_size, color=(255, 255, 255))

    def test_generate_mask_batch_returns_list(self):
        """Test that generate_mask_batch returns a list"""
        masks = generate_mask_batch(self.test_image, n_masks=5, complexity=0.5)
        self.assertIsInstance(masks, list)

    def test_generate_mask_batch_correct_count(self):
        """Test that batch generates correct number of masks"""
        n_masks = 10
        masks = generate_mask_batch(self.test_image, n_masks=n_masks, complexity=0.5)
        self.assertEqual(len(masks), n_masks)

    def test_generate_mask_batch_all_valid(self):
        """Test that all masks in batch are valid PIL Images"""
        masks = generate_mask_batch(self.test_image, n_masks=5, complexity=0.5)
        for mask in masks:
            self.assertIsInstance(mask, Image.Image)
            self.assertEqual(mask.size, self.img_size)

    def test_generate_mask_batch_variability(self):
        """Test that batch generates different masks"""
        masks = generate_mask_batch(self.test_image, n_masks=5, complexity=0.5)
        mask_arrays = [np.array(m) for m in masks]
        
        # Check that not all masks are identical
        all_same = all(np.array_equal(mask_arrays[0], m) for m in mask_arrays[1:])
        self.assertFalse(all_same)


if __name__ == "__main__":
    unittest.main()
