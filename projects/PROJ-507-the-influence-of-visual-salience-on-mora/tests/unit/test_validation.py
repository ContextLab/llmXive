"""
Unit tests for semantic preservation verification.
"""
import pytest
import numpy as np
from PIL import Image
import torch
from unittest.mock import patch, MagicMock

# Import the module
from validation import (
    verify_semantic_preservation,
    compute_laplacian_variance,
    crop_region,
    SemanticPreservationError,
    THRESHOLD_ROI_SIMILARITY,
    THRESHOLD_BG_SIMILARITY,
    THRESHOLD_TEXTURE_CHANGE
)

@pytest.fixture
def mock_images(tmp_path):
    """Create mock original and manipulated images."""
    # Create a simple image: 256x256 with a distinct ROI
    orig = Image.new('RGB', (256, 256), color=(100, 100, 100))
    # Draw a red square in the ROI
    roi_x, roi_y, roi_w, roi_h = 50, 50, 100, 100
    for x in range(roi_x, roi_x + roi_w):
        for y in range(roi_y, roi_y + roi_h):
            orig.putpixel((x, y), (255, 0, 0))

    # Manipulated image: Same content, slightly different luminance in ROI
    # We'll just make it slightly brighter in the ROI
    manip = Image.new('RGB', (256, 256), color=(100, 100, 100))
    for x in range(roi_x, roi_x + roi_w):
        for y in range(roi_y, roi_y + roi_h):
            # Increase brightness slightly (semantic preservation should hold)
            val = min(255, 255 - 10) # Slightly less red? Or just change luminance
            # Let's just change the green channel slightly to simulate luminance change without semantic shift
            manip.putpixel((x, y), (255, 10, 0))

    orig_path = tmp_path / "original.png"
    manip_path = tmp_path / "manipulated.png"
    orig.save(orig_path)
    manip.save(manip_path)

    return str(orig_path), str(manip_path), [roi_x, roi_y, roi_w, roi_h]

def test_crop_region_valid():
    """Test cropping a valid region."""
    img = Image.new('RGB', (100, 100), color=(10, 20, 30))
    crop = crop_region(img, [10, 10, 50, 50])
    assert crop.size == (50, 50)
    # Check a pixel
    assert crop.getpixel((0, 0)) == (10, 20, 30)

def test_crop_region_invalid():
    """Test cropping an invalid region (out of bounds or zero size)."""
    img = Image.new('RGB', (100, 100), color=(10, 20, 30))
    with pytest.raises(ValueError):
        crop_region(img, [100, 100, 10, 10]) # x + w > width

def test_laplacian_variance():
    """Test Laplacian variance calculation."""
    # Flat image -> variance ~ 0
    flat = np.zeros((100, 100), dtype=np.uint8)
    var_flat = compute_laplacian_variance(flat)
    assert var_flat < 1e-5

    # High edge image -> variance > 0
    # Create a checkerboard
    checker = np.zeros((100, 100), dtype=np.uint8)
    checker[::2, ::2] = 255
    checker[1::2, 1::2] = 255
    var_checker = compute_laplacian_variance(checker)
    assert var_checker > 1000 # Should be significant

@patch('validation.load_clip_model')
@patch('validation.compute_embedding')
@patch('validation.cosine_similarity')
def test_verify_semantic_preservation_passes(
    mock_sim, mock_emb, mock_load_model, mock_images
):
    """Test that verification passes when similarities are high."""
    orig_path, manip_path, bbox = mock_images

    # Mock embeddings
    mock_emb.return_value = torch.tensor([1.0, 0.0]) # Dummy embedding

    # Mock similarities to pass
    mock_sim.side_effect = [0.98, 0.995] # ROI sim, BG sim

    # Mock Laplacian variance to pass (change < 0.05)
    # We need to patch the internal call or the result.
    # Since compute_laplacian_variance is called inside, we can't easily mock it without patching the module.
    # Let's assume the images are such that the variance change is low.
    # For the test, we rely on the fact that the mock_images are simple.
    # But to be safe, we can patch the function in the module being tested.
    with patch('validation.compute_laplacian_variance') as mock_lap:
        mock_lap.side_effect = [100.0, 102.0] # Change = 2/100 = 0.02 < 0.05
        results = verify_semantic_preservation(orig_path, manip_path, bbox)
        assert results['overall_passed'] is True
        assert results['passed_roi'] is True
        assert results['passed_bg'] is True
        assert results['passed_texture'] is True

@patch('validation.load_clip_model')
@patch('validation.compute_embedding')
@patch('validation.cosine_similarity')
def test_verify_semantic_preservation_fails_roi(
    mock_sim, mock_emb, mock_load_model, mock_images
):
    """Test that verification fails when ROI similarity is low."""
    orig_path, manip_path, bbox = mock_images

    mock_emb.return_value = torch.tensor([1.0, 0.0])
    mock_sim.side_effect = [0.90, 0.995] # ROI sim < 0.95

    with patch('validation.compute_laplacian_variance') as mock_lap:
        mock_lap.side_effect = [100.0, 102.0]
        with pytest.raises(SemanticPreservationError, match="ROI similarity"):
            verify_semantic_preservation(orig_path, manip_path, bbox)

@patch('validation.load_clip_model')
@patch('validation.compute_embedding')
@patch('validation.cosine_similarity')
def test_verify_semantic_preservation_fails_bg(
    mock_sim, mock_emb, mock_load_model, mock_images
):
    """Test that verification fails when background similarity is low."""
    orig_path, manip_path, bbox = mock_images

    mock_emb.return_value = torch.tensor([1.0, 0.0])
    mock_sim.side_effect = [0.98, 0.98] # BG sim < 0.99

    with patch('validation.compute_laplacian_variance') as mock_lap:
        mock_lap.side_effect = [100.0, 102.0]
        with pytest.raises(SemanticPreservationError, match="Background similarity"):
            verify_semantic_preservation(orig_path, manip_path, bbox)

@patch('validation.load_clip_model')
@patch('validation.compute_embedding')
@patch('validation.cosine_similarity')
def test_verify_semantic_preservation_fails_texture(
    mock_sim, mock_emb, mock_load_model, mock_images
):
    """Test that verification fails when texture change is high."""
    orig_path, manip_path, bbox = mock_images

    mock_emb.return_value = torch.tensor([1.0, 0.0])
    mock_sim.side_effect = [0.98, 0.995]

    with patch('validation.compute_laplacian_variance') as mock_lap:
        # Change = |100 - 200| / 100 = 1.0 > 0.05
        mock_lap.side_effect = [100.0, 200.0]
        with pytest.raises(SemanticPreservationError, match="Texture change"):
            verify_semantic_preservation(orig_path, manip_path, bbox)