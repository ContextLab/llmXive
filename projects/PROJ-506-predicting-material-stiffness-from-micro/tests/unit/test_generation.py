"""
Unit tests for microstructure generation logic.

Tests for code/data_generation/generate_microstructures.py
"""
import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data_generation.generate_microstructures import (
    generate_microstructure,
    calculate_topological_metrics
)

def test_generate_microstructure_dimensions():
    """Test that generated microstructure has correct dimensions."""
    seed = 42
    image = generate_microstructure(seed=seed, size=128, density=0.3, topology="random_disks")
    assert image.shape == (128, 128), f"Expected (128, 128), got {image.shape}"
    assert image.dtype == np.uint8, f"Expected uint8, got {image.dtype}"

def test_generate_microstructure_density_range():
    """Test that generated microstructure respects density bounds."""
    for density in [0.1, 0.5, 0.9]:
        image = generate_microstructure(seed=42, size=128, density=density, topology="random_disks")
        # Calculate actual density
        actual_density = np.mean(image > 0)
        # Allow 10% tolerance
        assert abs(actual_density - density) < 0.1 * density, \
            f"Actual density {actual_density} differs from target {density}"

def test_generate_microstructure_reproducibility():
    """Test that same seed produces same result."""
    image1 = generate_microstructure(seed=42, size=128, density=0.3, topology="random_disks")
    image2 = generate_microstructure(seed=42, size=128, density=0.3, topology="random_disks")
    np.testing.assert_array_equal(image1, image2)

def test_generate_microstructure_different_seeds():
    """Test that different seeds produce different results."""
    image1 = generate_microstructure(seed=42, size=128, density=0.3, topology="random_disks")
    image2 = generate_microstructure(seed=123, size=128, density=0.3, topology="random_disks")
    assert not np.array_equal(image1, image2)

def test_calculate_topological_metrics_circle():
    """Test topological metrics for a perfect circle."""
    # Create a perfect circle mask
    size = 100
    y, x = np.ogrid[:size, :size]
    center = size // 2
    radius = 20
    mask = ((x - center)**2 + (y - center)**2 <= radius**2).astype(np.uint8)
    
    shape_factor, connectivity = calculate_topological_metrics(mask)
    
    # Shape factor should be close to 1.0 for a circle
    assert 0.9 < shape_factor <= 1.0, f"Shape factor {shape_factor} not close to 1.0"
    # Connectivity for a single disk should be positive
    assert connectivity > 0, f"Connectivity {connectivity} should be positive"

def test_calculate_topological_metrics_empty():
    """Test topological metrics for empty image."""
    empty_mask = np.zeros((100, 100), dtype=np.uint8)
    shape_factor, connectivity = calculate_topological_metrics(empty_mask)
    assert shape_factor == 0.0
    assert connectivity == 0.0
