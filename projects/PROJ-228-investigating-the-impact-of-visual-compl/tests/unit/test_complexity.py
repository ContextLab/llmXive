import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from complexity import calculate_entropy, calculate_fractal_dimension, calculate_texture_complexity, convolve_with_hrf, batch_process_complexity

# Create a temporary directory for test images
import tempfile
import shutil

@pytest.fixture
def temp_image_dir():
    """Create a temporary directory with test images."""
    temp_dir = tempfile.mkdtemp()
    
    # Create a simple test image (10x10 grayscale)
    from PIL import Image
    img = Image.new('L', (10, 10), color=128)
    img.save(os.path.join(temp_dir, 'test_image.png'))
    
    # Create a high-entropy image (random noise)
    random_img = Image.new('L', (10, 10), color=0)
    pixels = random_img.load()
    for i in range(10):
        for j in range(10):
            pixels[i, j] = np.random.randint(0, 256)
    random_img.save(os.path.join(temp_dir, 'random_image.png'))
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_entropy_returns_positive(temp_image_dir):
    """Test that calculate_entropy returns a positive value."""
    image_path = os.path.join(temp_image_dir, 'test_image.png')
    entropy = calculate_entropy(image_path)
    
    assert entropy >= 0, f"Entropy should be non-negative, got {entropy}"
    assert isinstance(entropy, float), f"Entropy should be float, got {type(entropy)}"

def test_entropy_high_vs_low(temp_image_dir):
    """Test that random image has higher entropy than uniform image."""
    uniform_path = os.path.join(temp_image_dir, 'test_image.png')
    random_path = os.path.join(temp_image_dir, 'random_image.png')
    
    entropy_uniform = calculate_entropy(uniform_path)
    entropy_random = calculate_entropy(random_path)
    
    # Random image should have higher entropy (more information)
    assert entropy_random > entropy_uniform, f"Random image entropy ({entropy_random}) should be > uniform ({entropy_uniform})"

def test_fractal_dim_returns_positive(temp_image_dir):
    """Test that calculate_fractal_dimension returns a positive value."""
    image_path = os.path.join(temp_image_dir, 'test_image.png')
    fractal_dim = calculate_fractal_dimension(image_path)
    
    assert fractal_dim >= 0, f"Fractal dimension should be non-negative, got {fractal_dim}"
    assert isinstance(fractal_dim, float), f"Fractal dimension should be float, got {type(fractal_dim)}"

def test_fractal_dim_reasonable_range(temp_image_dir):
    """Test that fractal dimension is within reasonable bounds (0 to 3 for 2D images)."""
    image_path = os.path.join(temp_image_dir, 'test_image.png')
    fractal_dim = calculate_fractal_dimension(image_path)
    
    assert 0 <= fractal_dim <= 3, f"Fractal dimension should be between 0 and 3, got {fractal_dim}"

def test_texture_complexity_returns_dict(temp_image_dir):
    """Test that calculate_texture_complexity returns a dictionary with expected keys."""
    image_path = os.path.join(temp_image_dir, 'test_image.png')
    texture_props = calculate_texture_complexity(image_path)
    
    assert isinstance(texture_props, dict), f"Should return dict, got {type(texture_props)}"
    
    expected_keys = ['contrast', 'dissimilarity', 'homogeneity', 'energy', 'correlation', 'asm']
    for key in expected_keys:
        assert key in texture_props, f"Missing key: {key}"
        assert isinstance(texture_props[key], float), f"Value for {key} should be float"

def test_convolve_with_hrf_shape():
    """Test that convolve_with_hrf returns output of correct shape."""
    time_series = [1.0, 2.0, 3.0, 4.0, 5.0]
    convolved = convolve_with_hrf(time_series)
    
    assert len(convolved) == len(time_series), f"Output length {len(convolved)} should match input length {len(time_series)}"
    assert all(isinstance(x, float) for x in convolved), "All output values should be float"

def test_convolve_with_hrf_empty_input():
    """Test that convolve_with_hrf handles empty input."""
    convolved = convolve_with_hrf([])
    assert convolved == [], f"Empty input should return empty list, got {convolved}"

def test_convolve_with_hrf_single_value():
    """Test that convolve_with_hrf handles single value input."""
    time_series = [1.0]
    convolved = convolve_with_hrf(time_series)
    assert len(convolved) == 1, f"Single value input should return single value output, got {len(convolved)}"

def test_batch_process_complexity_creates_file(temp_image_dir):
    """Test that batch_process_complexity creates the output file."""
    output_file = os.path.join(tempfile.gettempdir(), 'test_complexity_output.csv')
    
    # Clean up if exists
    if os.path.exists(output_file):
        os.remove(output_file)
    
    stats = batch_process_complexity(
        input_dir=temp_image_dir,
        output_file=output_file,
        batch_size=10
    )
    
    assert os.path.exists(output_file), f"Output file {output_file} should exist"
    assert stats['processed'] > 0, f"Should have processed some files, got {stats['processed']}"
    
    # Clean up
    if os.path.exists(output_file):
        os.remove(output_file)

def test_batch_process_complexity_empty_dir():
    """Test that batch_process_complexity handles empty directory."""
    temp_dir = tempfile.mkdtemp()
    output_file = os.path.join(tempfile.gettempdir(), 'test_empty_output.csv')
    
    try:
        stats = batch_process_complexity(
            input_dir=temp_dir,
            output_file=output_file,
            batch_size=10
        )
        
        assert stats['total_files'] == 0, f"Should find 0 files, got {stats['total_files']}"
        assert stats['processed'] == 0, f"Should process 0 files, got {stats['processed']}"
    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        if os.path.exists(output_file):
            os.remove(output_file)

def test_entropy_file_not_found():
    """Test that calculate_entropy raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        calculate_entropy("nonexistent_file.png")

def test_fractal_dim_file_not_found():
    """Test that calculate_fractal_dimension raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        calculate_fractal_dimension("nonexistent_file.png")

def test_texture_complexity_file_not_found():
    """Test that calculate_texture_complexity raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        calculate_texture_complexity("nonexistent_file.png")
