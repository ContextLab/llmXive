"""
Unit tests for code/data/preprocessing.py
"""

import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import torch
from PIL import Image

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.preprocessing import (
    load_image,
    resize_image,
    normalize_image,
    image_to_tensor,
    load_and_preprocess_image,
    detect_and_clamp_nans,
    ImagePreprocessingError,
    DEFAULT_IMAGE_SIZE,
    DEFAULT_MEAN,
    DEFAULT_STD
)

class TestLoadImage(unittest.TestCase):
    """Tests for load_image function."""
    
    def setUp(self):
        # Create a temporary image file
        self.temp_dir = tempfile.mkdtemp()
        self.image_path = os.path.join(self.temp_dir, "test.png")
        
        # Create a simple test image
        img = Image.new("RGB", (100, 100), color="red")
        img.save(self.image_path)
    
    def tearDown(self):
        # Clean up
        if os.path.exists(self.image_path):
            os.remove(self.image_path)
        os.rmdir(self.temp_dir)
    
    def test_load_rgb_image(self):
        """Test loading an RGB image."""
        img = load_image(self.image_path, mode="RGB")
        self.assertEqual(img.mode, "RGB")
        self.assertEqual(img.size, (100, 100))
    
    def test_load_grayscale_conversion(self):
        """Test loading and converting to grayscale."""
        img = load_image(self.image_path, mode="L")
        self.assertEqual(img.mode, "L")
    
    def test_load_nonexistent_image(self):
        """Test that loading a nonexistent image raises an error."""
        with self.assertRaises(ImagePreprocessingError):
            load_image("nonexistent.png")
    
    def test_load_corrupted_image(self):
        """Test that loading a corrupted file raises an error."""
        corrupted_path = os.path.join(self.temp_dir, "corrupted.png")
        with open(corrupted_path, "w") as f:
            f.write("not an image")
        
        with self.assertRaises(ImagePreprocessingError):
            load_image(corrupted_path)

class TestResizeImage(unittest.TestCase):
    """Tests for resize_image function."""
    
    def test_resize_image(self):
        """Test resizing an image."""
        img = Image.new("RGB", (100, 100))
        resized = resize_image(img, size=(224, 224))
        self.assertEqual(resized.size, (224, 224))
    
    def test_resize_non_square(self):
        """Test resizing to non-square dimensions."""
        img = Image.new("RGB", (100, 100))
        resized = resize_image(img, size=(256, 128))
        self.assertEqual(resized.size, (256, 128))

class TestNormalizeImage(unittest.TestCase):
    """Tests for normalize_image function."""
    
    def test_normalize_rgb(self):
        """Test normalization of RGB image."""
        img = Image.new("RGB", (10, 10), color="white")
        normalized = normalize_image(img)
        
        self.assertEqual(normalized.shape, (3, 10, 10))
        self.assertTrue(np.allclose(normalized, 0, atol=0.1))  # White should be near 0 after normalization
    
    def test_normalize_grayscale(self):
        """Test normalization of grayscale image (converted to RGB)."""
        img = Image.new("L", (10, 10), color=128)
        normalized = normalize_image(img)
        
        self.assertEqual(normalized.shape, (3, 10, 10))

class TestImageToTensor(unittest.TestCase):
    """Tests for image_to_tensor function."""
    
    def test_image_to_tensor_shape(self):
        """Test that output tensor has correct shape."""
        img = Image.new("RGB", (100, 100))
        tensor = image_to_tensor(img, size=(224, 224))
        
        self.assertEqual(tensor.shape, (1, 3, 224, 224))
    
    def test_image_to_tensor_dtype(self):
        """Test that output tensor has correct dtype."""
        img = Image.new("RGB", (100, 100))
        tensor = image_to_tensor(img)
        
        self.assertEqual(tensor.dtype, torch.float32)
    
    def test_image_to_tensor_nan_clamping(self):
        """Test that NaN values are clamped."""
        img = Image.new("RGB", (100, 100))
        tensor = image_to_tensor(img, clamp_nans=True)
        
        self.assertFalse(torch.isnan(tensor).any())

class TestDetectAndClampNans(unittest.TestCase):
    """Tests for detect_and_clamp_nans function."""
    
    def test_no_nans(self):
        """Test tensor with no NaNs."""
        tensor = torch.randn(3, 224, 224)
        result = detect_and_clamp_nans(tensor)
        self.assertTrue(torch.equal(result, tensor))
    
    def test_with_nans(self):
        """Test tensor with NaNs."""
        tensor = torch.randn(3, 224, 224)
        tensor[0, 0, 0] = float('nan')
        
        result = detect_and_clamp_nans(tensor)
        self.assertFalse(torch.isnan(result).any())
        self.assertEqual(result[0, 0, 0], 0.0)

class TestLoadAndPreprocessImage(unittest.TestCase):
    """Tests for load_and_preprocess_image function."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.image_path = os.path.join(self.temp_dir, "test.png")
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(self.image_path)
    
    def tearDown(self):
        if os.path.exists(self.image_path):
            os.remove(self.image_path)
        os.rmdir(self.temp_dir)
    
    def test_load_and_preprocess(self):
        """Test loading and preprocessing a single image."""
        tensor = load_and_preprocess_image(self.image_path, size=(224, 224))
        
        self.assertEqual(tensor.shape, (1, 3, 224, 224))
        self.assertFalse(torch.isnan(tensor).any())

if __name__ == "__main__":
    unittest.main()