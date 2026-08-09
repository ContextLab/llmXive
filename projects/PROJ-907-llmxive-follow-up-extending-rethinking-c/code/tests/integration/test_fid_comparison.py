import pytest
import torch
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.metrics import calculate_fid

class TestFIDComparison:
    """Integration tests for FID calculation between model outputs."""

    def test_fid_calculation_on_dummy_samples(self):
        """Test FID calculation on dummy image samples."""
        # Create dummy image tensors (batch_size, channels, height, width)
        # Using small sizes for CPU compatibility
        batch_size = 16
        channels = 3
        height = 64
        width = 64
        
        # Generate random dummy images for two sets
        torch.manual_seed(42)
        images_1 = torch.randn(batch_size, channels, height, width)
        images_2 = torch.randn(batch_size, channels, height, width)
        
        # Calculate FID
        fid_score = calculate_fid(images_1, images_2)
        
        # FID should be a non-negative float
        assert isinstance(fid_score, float), f"FID should return float, got {type(fid_score)}"
        assert fid_score >= 0, f"FID should be non-negative, got {fid_score}"
        assert not np.isnan(fid_score), "FID should not be NaN"
        assert not np.isinf(fid_score), "FID should not be infinite"
        
        print(f"Test passed: FID score = {fid_score:.4f}")

    def test_fid_calculation_edge_cases(self):
        """Test FID calculation with edge cases."""
        # Test with identical images (should be close to 0)
        batch_size = 8
        channels = 3
        height = 32
        width = 32
        
        torch.manual_seed(123)
        base_images = torch.randn(batch_size, channels, height, width)
        
        # Identical images
        fid_identical = calculate_fid(base_images, base_images)
        assert fid_identical < 0.1, f"Identical images should have FID < 0.1, got {fid_identical}"
        
        # Test with very different images
        different_images = torch.randn(batch_size, channels, height, width) * 10 + 50
        fid_different = calculate_fid(base_images, different_images)
        assert fid_different > fid_identical, "Different images should have higher FID"
        
        # Test with single image
        single_image_1 = torch.randn(1, channels, height, width)
        single_image_2 = torch.randn(1, channels, height, width)
        fid_single = calculate_fid(single_image_1, single_image_2)
        assert isinstance(fid_single, float), "FID with single image should return float"
        
        print(f"Edge case tests passed: identical={fid_identical:.4f}, different={fid_different:.4f}, single={fid_single:.4f}")

    def test_fid_with_realistic_shapes(self):
        """Test FID with shapes closer to real model outputs."""
        # Simulate typical diffusion model output shapes
        batch_size = 4
        channels = 3
        height = 128
        width = 128
        
        torch.manual_seed(456)
        images_1 = torch.rand(batch_size, channels, height, width)  # Normalized [0, 1]
        images_2 = torch.rand(batch_size, channels, height, width)
        
        fid_score = calculate_fid(images_1, images_2)
        
        assert isinstance(fid_score, float)
        assert 0 <= fid_score < 100, f"Reasonable FID should be < 100, got {fid_score}"
        
        print(f"Realistic shape test passed: FID = {fid_score:.4f}")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])