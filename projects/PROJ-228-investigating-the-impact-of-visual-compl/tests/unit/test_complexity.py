"""
Unit tests for the complexity analysis module.
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
from PIL import Image

from code.complexity import (
    calculate_entropy,
    calculate_fractal_dimension,
    calculate_texture_complexity,
    batch_process_complexity
)


@pytest.fixture
def test_image_rgb(tmp_path):
    """Create a simple RGB test image."""
    img = Image.new('RGB', (100, 100), color=(73, 109, 137))
    # Add some variation
    for i in range(10):
        for j in range(10):
            img.putpixel((i * 10, j * 10), (255, 0, 0))
    path = tmp_path / "test_rgb.png"
    img.save(path)
    return path


@pytest.fixture
def test_image_gray(tmp_path):
    """Create a simple grayscale test image."""
    img = Image.new('L', (100, 100), color=128)
    # Add some variation
    for i in range(10):
        for j in range(10):
            img.putpixel((i * 10, j * 10), 255)
    path = tmp_path / "test_gray.png"
    img.save(path)
    return path


@pytest.fixture
def test_image_noisy(tmp_path):
    """Create a noisy test image (higher entropy)."""
    img_array = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
    img = Image.fromarray(img_array)
    path = tmp_path / "test_noisy.png"
    img.save(path)
    return path


def test_calculate_entropy_returns_positive(test_image_rgb):
    """Test that calculate_entropy returns a positive float."""
    entropy_val = calculate_entropy(test_image_rgb)
    assert isinstance(entropy_val, float)
    assert entropy_val > 0
    assert entropy_val <= 8.0  # Max for 8-bit image is 8 bits


def test_calculate_entropy_noisy_image(test_image_noisy):
    """Test that noisy image has higher entropy than uniform image."""
    entropy_noisy = calculate_entropy(test_image_noisy)
    # Create a uniform image for comparison
    uniform_img = Image.new('L', (100, 100), color=128)
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        uniform_path = Path(f.name)
    uniform_img.save(uniform_path)
    
    entropy_uniform = calculate_entropy(uniform_path)
    
    assert entropy_noisy > entropy_uniform
    
    # Cleanup
    uniform_path.unlink()


def test_calculate_fractal_dimension_returns_positive(test_image_rgb):
    """Test that calculate_fractal_dimension returns a positive float."""
    fractal_val = calculate_fractal_dimension(test_image_rgb)
    assert isinstance(fractal_val, float)
    assert fractal_val > 0
    # Fractal dimension for 2D images is typically between 1 and 2


def test_calculate_texture_complexity_structure(test_image_rgb):
    """Test that calculate_texture_complexity returns expected structure."""
    result = calculate_texture_complexity(test_image_rgb)
    
    assert isinstance(result, dict)
    assert 'contrast' in result
    assert 'correlation' in result
    assert 'energy' in result
    assert 'homogeneity' in result
    assert 'composite_score' in result
    
    # All values should be floats
    for key, value in result.items():
        assert isinstance(value, float)


def test_batch_process_complexity(test_image_rgb, test_image_gray, test_image_noisy):
    """Test batch processing of multiple images."""
    images = [test_image_rgb, test_image_gray, test_image_noisy]
    results = batch_process_complexity(images)
    
    assert len(results) == 3
    
    for result in results:
        assert 'path' in result
        assert 'entropy' in result
        assert 'fractal_dimension' in result
        assert 'composite_score' in result
        assert result['entropy'] > 0
        assert result['fractal_dimension'] > 0


def test_file_not_found_error():
    """Test that FileNotFoundError is raised for missing files."""
    with pytest.raises(FileNotFoundError):
        calculate_entropy("nonexistent_image.png")


def test_invalid_image_handling(tmp_path):
    """Test handling of invalid image files."""
    invalid_path = tmp_path / "invalid.png"
    invalid_path.write_text("not an image")
    
    with pytest.raises(Exception):
        calculate_entropy(invalid_path)