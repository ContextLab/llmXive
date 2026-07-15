"""
Unit tests for the metrics module.
"""
import pytest
import numpy as np
import torch
from src.metrics import calculate_fid, _preprocess_images, _load_inception_model

class TestCalculateFID:
    """Tests for the calculate_fid function."""
    
    def test_fid_with_identical_images(self):
        """FID should be 0 (or very close) for identical images."""
        # Create identical images
        img = np.random.randint(0, 255, (299, 299, 3), dtype=np.uint8)
        images = [img.copy() for _ in range(10)]
        
        fid = calculate_fid(images, images)
        
        # FID should be very small (ideally 0, but floating point errors)
        assert fid >= 0
        assert fid < 1e-6, f"FID for identical images should be ~0, got {fid}"
    
    def test_fid_with_different_images(self):
        """FID should be positive for different images."""
        images_1 = [np.random.randint(0, 255, (299, 299, 3), dtype=np.uint8) for _ in range(10)]
        images_2 = [np.random.randint(0, 255, (299, 299, 3), dtype=np.uint8) for _ in range(10)]
        
        fid = calculate_fid(images_1, images_2)
        
        assert fid >= 0, "FID should be non-negative"
    
    def test_fid_with_torch_tensors(self):
        """FID should work with torch tensors as input."""
        images_1 = [torch.rand(299, 299, 3) for _ in range(5)]
        images_2 = [torch.rand(299, 299, 3) for _ in range(5)]
        
        fid = calculate_fid(images_1, images_2)
        
        assert isinstance(fid, float)
        assert fid >= 0
    
    def test_fid_empty_list_raises_error(self):
        """FID should raise ValueError for empty image lists."""
        with pytest.raises(ValueError):
            calculate_fid([], [])
    
    def test_fid_mismatched_sizes_raises_error(self):
        """FID should raise ValueError for mismatched list sizes."""
        images_1 = [np.random.randint(0, 255, (299, 299, 3), dtype=np.uint8) for _ in range(5)]
        images_2 = [np.random.randint(0, 255, (299, 299, 3), dtype=np.uint8) for _ in range(10)]
        
        with pytest.raises(ValueError):
            calculate_fid(images_1, images_2)
    
    def test_fid_returns_float(self):
        """FID should return a float value."""
        images_1 = [np.random.randint(0, 255, (299, 299, 3), dtype=np.uint8) for _ in range(5)]
        images_2 = [np.random.randint(0, 255, (299, 299, 3), dtype=np.uint8) for _ in range(5)]
        
        fid = calculate_fid(images_1, images_2)
        
        assert isinstance(fid, float)

class TestPreprocessImages:
    """Tests for the _preprocess_images function."""
    
    def test_preprocess_numpy_uint8(self):
        """Should correctly preprocess numpy uint8 images."""
        images = [np.random.randint(0, 255, (299, 299, 3), dtype=np.uint8) for _ in range(5)]
        processed = _preprocess_images(images)
        
        assert processed.shape == (5, 3, 299, 299)
        assert processed.dtype == torch.float32
    
    def test_preprocess_torch_float(self):
        """Should correctly preprocess torch float images."""
        images = [torch.rand(299, 299, 3) for _ in range(5)]
        processed = _preprocess_images(images)
        
        assert processed.shape == (5, 3, 299, 299)
        assert processed.dtype == torch.float32
    
    def test_preprocess_resizes_images(self):
        """Should resize images to 299x299."""
        # Create images of different sizes
        images = [
            np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8),
            np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8),
        ]
        processed = _preprocess_images(images)
        
        assert processed.shape == (2, 3, 299, 299)
    
    def test_preprocess_handles_grayscale(self):
        """Should handle grayscale images by repeating channels."""
        images = [np.random.randint(0, 255, (299, 299), dtype=np.uint8) for _ in range(3)]
        processed = _preprocess_images(images)
        
        assert processed.shape == (3, 3, 299, 299)

class TestLoadInceptionModel:
    """Tests for the _load_inception_model function."""
    
    def test_model_is_eval_mode(self):
        """Model should be in eval mode."""
        model = _load_inception_model()
        assert model.training == False
    
    def test_model_requires_grad_false(self):
        """Model parameters should not require gradients."""
        model = _load_inception_model()
        for param in model.parameters():
            assert param.requires_grad == False
    
    def test_model_is_on_cpu(self):
        """Model should be on CPU."""
        model = _load_inception_model()
        # Check if model parameters are on CPU
        for param in model.parameters():
            assert param.device.type == 'cpu'