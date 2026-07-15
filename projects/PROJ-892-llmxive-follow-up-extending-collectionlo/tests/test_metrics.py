"""
Unit tests for code/metrics.py functions.

These tests verify the correctness of CLIP embedding extraction,
cosine similarity computation, LPIPS distance, and CESR score calculation.
"""
import torch
import numpy as np
from PIL import Image
from io import BytesIO
import pytest
from pathlib import Path

# Import the functions to test
from metrics import (
    extract_clip_image_embedding,
    extract_clip_text_embedding,
    compute_cosine_similarity,
    compute_image_text_similarity,
    compute_lpips_distance,
    compute_cesr_score
)

@pytest.fixture
def sample_image():
    """Create a simple synthetic test image."""
    # Create a 224x224 RGB image with random values
    img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    return Image.fromarray(img_array)

@pytest.fixture
def sample_text():
    """Sample text for embedding extraction."""
    return "a photo of a cat"

def test_extract_clip_text_embedding(sample_text):
    """Test that text embedding extraction returns a valid tensor."""
    embedding = extract_clip_text_embedding(sample_text)
    assert embedding is not None
    assert isinstance(embedding, torch.Tensor)
    assert embedding.dim() == 1  # Should be a 1D vector

def test_extract_clip_image_embedding(sample_image):
    """Test that image embedding extraction returns a valid tensor."""
    embedding = extract_clip_image_embedding(sample_image)
    assert embedding is not None
    assert isinstance(embedding, torch.Tensor)
    assert embedding.dim() == 1  # Should be a 1D vector

def test_compute_cosine_similarity():
    """Test cosine similarity between two identical vectors is 1.0."""
    vec1 = torch.tensor([1.0, 2.0, 3.0])
    vec2 = torch.tensor([1.0, 2.0, 3.0])
    similarity = compute_cosine_similarity(vec1, vec2)
    assert abs(similarity.item() - 1.0) < 1e-6

def test_compute_cosine_similarity_opposite():
    """Test cosine similarity between opposite vectors is -1.0."""
    vec1 = torch.tensor([1.0, 0.0, 0.0])
    vec2 = torch.tensor([-1.0, 0.0, 0.0])
    similarity = compute_cosine_similarity(vec1, vec2)
    assert abs(similarity.item() - (-1.0)) < 1e-6

def test_compute_image_text_similarity(sample_image, sample_text):
    """Test end-to-end image-text similarity computation."""
    similarity = compute_image_text_similarity(sample_image, sample_text)
    assert -1.0 <= similarity <= 1.0

def test_compute_lpips_distance(sample_image):
    """Test LPIPS distance computation (should be non-negative)."""
    # LPIPS distance between an image and itself should be 0
    distance = compute_lpips_distance(sample_image, sample_image)
    assert distance >= 0.0
    # Due to numerical precision, it might not be exactly 0
    assert distance < 0.01

def test_compute_cesr_score():
    """Test CESR score computation with mock data."""
    # Mock embeddings: target and reference
    target_embedding = torch.tensor([1.0, 0.0, 0.0])
    reference_embeddings = [
        torch.tensor([0.0, 1.0, 0.0]),  # Different concept
        torch.tensor([0.0, 0.0, 1.0])   # Different concept
    ]
    
    cesr = compute_cesr_score(target_embedding, reference_embeddings)
    
    # CESR should be a ratio between 0 and 1
    assert 0.0 <= cesr <= 1.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])