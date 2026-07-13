"""
Unit tests for mask generator metrics calculation.
Tests gradient_variance and texture_entropy computation.
"""
import numpy as np
import torch
from code.data.mask_generator import (
    _calculate_gradient_variance,
    _calculate_texture_entropy,
    generate_mask
)


def test_gradient_variance_constant():
    """Test that a constant image has near-zero gradient variance."""
    image = torch.ones(100, 100)
    variance = _calculate_gradient_variance(image)
    assert variance < 0.01, f"Expected near-zero variance for constant image, got {variance}"


def test_gradient_variance_edges():
    """Test that an image with sharp edges has higher gradient variance."""
    image = torch.zeros(100, 100)
    image[:, 50:] = 1.0  # Sharp vertical edge
    variance = _calculate_gradient_variance(image)
    assert variance > 0.01, f"Expected higher variance for edge image, got {variance}"


def test_texture_entropy_uniform():
    """Test entropy on a uniform noise image."""
    image = torch.rand(100, 100)
    entropy = _calculate_texture_entropy(image)
    assert 0.0 <= entropy <= 1.0, f"Entropy should be in [0, 1], got {entropy}"


def test_generate_mask_output_shape():
    """Test that generated mask has correct shape."""
    width, height = 256, 256
    mask, metrics = generate_mask((width, height))
    assert mask.shape == (height, width), f"Expected shape ({height}, {width}), got {mask.shape}"


def test_generate_mask_metrics_keys():
    """Test that metrics dictionary contains required keys."""
    mask, metrics = generate_mask((256, 256))
    assert 'gradient_variance' in metrics, "Missing gradient_variance in metrics"
    assert 'texture_entropy' in metrics, "Missing texture_entropy in metrics"
    assert 'mask_ratio' in metrics, "Missing mask_ratio in metrics"
    assert 'num_shapes' in metrics, "Missing num_shapes in metrics"


def test_generate_mask_valid_range():
    """Test that mask ratio is within expected bounds."""
    mask, metrics = generate_mask((256, 256))
    ratio = metrics['mask_ratio']
    assert 0.05 <= ratio <= 0.50, f"Mask ratio {ratio} out of expected range [0.05, 0.50]"


def test_generate_mask_binary_values():
    """Test that mask contains only binary values (0 or 255)."""
    mask, _ = generate_mask((256, 256))
    unique_values = np.unique(mask)
    assert set(unique_values).issubset({0, 255}), f"Mask contains non-binary values: {unique_values}"