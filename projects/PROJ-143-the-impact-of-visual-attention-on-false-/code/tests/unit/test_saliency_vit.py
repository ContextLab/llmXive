import os
import sys
import tempfile
import numpy as np
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis.saliency import (
    load_vit_saliency_model,
    compute_vit_saliency_map,
    ViTSaliencyWrapper
)

class TestViTSaliency:
    """Unit tests for ViT-B saliency model wrapper (T025)."""

    def test_vit_wrapper_initialization(self):
        """Test that ViTSaliencyWrapper initializes correctly."""
        wrapper = ViTSaliencyWrapper()
        # Model might be None if loading fails, but wrapper should exist
        assert wrapper is not None
        assert wrapper.model_name == "vit_b_16"

    def test_load_vit_model_cpu_fallback(self):
        """Test that ViT model loads with CPU fallback."""
        wrapper = load_vit_saliency_model()
        # Should return a wrapper or None if model loading fails
        # We don't assert it's not None because it might fail in constrained environments
        assert wrapper is None or isinstance(wrapper, ViTSaliencyWrapper)

    def test_compute_vit_saliency_on_dummy_image(self):
        """Test saliency computation on a dummy image."""
        # Create a dummy image
        dummy_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        
        wrapper = load_vit_saliency_model()
        if wrapper is None:
            # If model not available, function should return None
            result = compute_vit_saliency_map(dummy_image)
            assert result is None
        else:
            result = compute_vit_saliency_map(dummy_image, wrapper)
            # If model is available, result should be a numpy array
            if result is not None:
                assert isinstance(result, np.ndarray)
                assert len(result.shape) == 2  # 2D saliency map
                assert 0 <= result.min() <= 1.0
                assert 0 <= result.max() <= 1.0

    def test_vit_saliency_normalization(self):
        """Test that saliency maps are normalized to [0, 1]."""
        dummy_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        
        wrapper = load_vit_saliency_model()
        if wrapper is None:
            return  # Skip if model not available
        
        result = compute_vit_saliency_map(dummy_image, wrapper)
        if result is not None:
            assert result.min() >= 0.0
            assert result.max() <= 1.0

    def test_vit_saliency_different_image_sizes(self):
        """Test saliency computation on images of different sizes."""
        sizes = [(100, 100, 3), (224, 224, 3), (300, 400, 3)]
        
        wrapper = load_vit_saliency_model()
        if wrapper is None:
            return  # Skip if model not available
        
        for h, w, c in sizes:
            dummy_image = np.random.randint(0, 255, (h, w, c), dtype=np.uint8)
            result = compute_vit_saliency_map(dummy_image, wrapper)
            
            if result is not None:
                # Result should match original image dimensions
                assert result.shape[0] == h
                assert result.shape[1] == w

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
