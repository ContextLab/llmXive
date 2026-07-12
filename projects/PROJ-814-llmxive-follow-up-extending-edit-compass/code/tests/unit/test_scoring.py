"""
Unit tests for scoring functionality.
"""
import pytest
import numpy as np
from PIL import Image
import tempfile
import os
from unittest.mock import patch, MagicMock

def test_ssim_calculation():
    """Assert SSIM calculation on dummy images returns value in [0, 1]."""
    from src.services.scoring import calculate_ssim
    
    # Create two identical images
    img1 = Image.new('RGB', (512, 512), color='red')
    img2 = Image.new('RGB', (512, 512), color='red')
    
    with tempfile.TemporaryDirectory() as tmpdir:
        path1 = os.path.join(tmpdir, 'img1.png')
        path2 = os.path.join(tmpdir, 'img2.png')
        img1.save(path1)
        img2.save(path2)
        
        ssim_score = calculate_ssim(path1, path2)
        assert 0 <= ssim_score <= 1

def test_lpips_calculation():
    """Assert LPIPS calculation on dummy images returns value in [0, 1]."""
    from src.services.scoring import calculate_lpips
    
    # Create two identical images
    img1 = Image.new('RGB', (512, 512), color='blue')
    img2 = Image.new('RGB', (512, 512), color='blue')
    
    with tempfile.TemporaryDirectory() as tmpdir:
        path1 = os.path.join(tmpdir, 'img1.png')
        path2 = os.path.join(tmpdir, 'img2.png')
        img1.save(path1)
        img2.save(path2)
        
        lpips_score = calculate_lpips(path1, path2)
        assert 0 <= lpips_score <= 1

def test_vlm_description_generation():
    """Assert VLM wrapper returns a non-empty string description for a valid image prompt."""
    from src.models.vlm import VLMWrapper
    
    # Create a dummy image
    img = Image.new('RGB', (512, 512), color='green')
    
    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = os.path.join(tmpdir, 'dummy.png')
        img.save(img_path)
        
        # Mock the underlying model to avoid needing a real GGUF file for this unit test
        # while verifying the wrapper's logic handles a valid response correctly.
        mock_model = MagicMock()
        # Simulate a valid model output
        mock_model.__call__ = MagicMock(return_value="A green square on a white background.")
        
        with patch('src.models.vlm.CppGgmlModel.from_file', return_value=mock_model):
            wrapper = VLMWrapper(model_path="dummy_path.gguf")
            # Force reload of the model in the wrapper to use our mock
            wrapper.model = mock_model
            
            description = wrapper.describe_image(img_path)
            
            # Assert the returned description is a non-empty string
            assert isinstance(description, str)
            assert len(description) > 0
            assert description == "A green square on a white background."

def test_logic_score_range():
    """Assert Logic Score (cosine similarity) is in [-1, 1]."""
    from src.services.scoring import calculate_logic_score
    
    # Test with dummy embeddings
    embedding1 = np.array([1.0, 0.0, 0.0])
    embedding2 = np.array([0.0, 1.0, 0.0])
    
    score = calculate_logic_score(embedding1, embedding2)
    assert -1 <= score <= 1
    
    # Test with identical embeddings
    score_identical = calculate_logic_score(embedding1, embedding1)
    assert score_identical == 1.0
    
    # Test with opposite embeddings
    embedding3 = np.array([-1.0, 0.0, 0.0])
    score_opposite = calculate_logic_score(embedding1, embedding3)
    assert score_opposite == -1.0
    
    # Test with random embeddings to ensure it stays within bounds
    rand1 = np.random.randn(384)
    rand2 = np.random.randn(384)
    score_random = calculate_logic_score(rand1, rand2)
    assert -1 <= score_random <= 1