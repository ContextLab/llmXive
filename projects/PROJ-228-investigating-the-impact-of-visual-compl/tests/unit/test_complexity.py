"""
Unit tests for the complexity module.
Tests are designed to fail initially to ensure TDD compliance.
"""
import pytest
from pathlib import Path
import numpy as np
from PIL import Image
import os
import tempfile

# Import the function under test from the sibling module
# Based on provided API surface: code/complexity.py defines calculate_entropy, calculate_fractal_dimension, convolve_with_hrf
from code.complexity import calculate_entropy, calculate_fractal_dimension, convolve_with_hrf


def test_entropy_returns_positive():
    """
    Test that calculate_entropy returns a positive value for a valid image.
    This test is designed to fail before the implementation is complete.
    """
    # Create a temporary directory and a mock image file
    with tempfile.TemporaryDirectory() as tmp_dir:
        mock_path = Path(tmp_dir) / "mock_image.png"
        
        # Create a simple valid grayscale image (10x10)
        # Using a simple pattern to ensure non-zero entropy
        data = np.random.randint(0, 256, (10, 10), dtype=np.uint8)
        img = Image.fromarray(data, mode='L')
        img.save(mock_path)
        
        # Call the function
        result = calculate_entropy(mock_path)
        
        # Assert the result is a positive number
        # The implementation must ensure entropy > 0 for a real image
        assert result > 0, f"Expected positive entropy, got {result}"
        
        # Additional sanity checks
        assert isinstance(result, float), "Entropy should be returned as a float"
        assert not np.isnan(result), "Entropy should not be NaN"
        assert not np.isinf(result), "Entropy should not be Inf"


def test_entropy_handles_uniform_image():
    """
    Test that a uniform image (all same pixel values) has entropy close to 0.
    This validates the mathematical correctness of the implementation.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        mock_path = Path(tmp_dir) / "uniform_image.png"
        
        # Create a uniform image
        data = np.ones((10, 10), dtype=np.uint8) * 128
        img = Image.fromarray(data, mode='L')
        img.save(mock_path)
        
        result = calculate_entropy(mock_path)
        
        # Uniform image should have very low or zero entropy
        assert result >= 0, "Entropy cannot be negative"
        # Depending on implementation (e.g., smoothing or binning), it might be slightly > 0
        # but should be significantly lower than a random image
        assert result < 0.1, f"Uniform image entropy should be near 0, got {result}"


def test_entropy_nonexistent_file():
    """
    Test that calculate_entropy raises an appropriate error for a non-existent file.
    """
    mock_path = Path("/tmp/nonexistent_image_12345.png")
    
    with pytest.raises((FileNotFoundError, ValueError, OSError)):
        calculate_entropy(mock_path)


def test_fractal_dim_returns_positive():
    """
    Test that calculate_fractal_dimension returns a positive value for a valid image.
    This test is designed to fail before the implementation is complete.
    """
    # Create a temporary directory and a mock image file
    with tempfile.TemporaryDirectory() as tmp_dir:
        mock_path = Path(tmp_dir) / "mock_fractal_image.png"
        
        # Create a simple valid grayscale image (64x64)
        # Using a pattern that has some complexity but is deterministic
        # A checkerboard pattern or noise ensures non-trivial fractal dimension
        data = np.random.randint(0, 256, (64, 64), dtype=np.uint8)
        img = Image.fromarray(data, mode='L')
        img.save(mock_path)
        
        # Call the function
        result = calculate_fractal_dimension(mock_path)
        
        # Assert the result is a positive number
        # Fractal dimension for 2D images is typically between 1.0 and 3.0
        assert result > 0, f"Expected positive fractal dimension, got {result}"
        
        # Additional sanity checks
        assert isinstance(result, float), "Fractal dimension should be returned as a float"
        assert not np.isnan(result), "Fractal dimension should not be NaN"
        assert not np.isinf(result), "Fractal dimension should not be Inf"
        # Fractal dimension for 2D images is typically between 1.0 and 3.0
        assert 1.0 <= result <= 3.0, f"Fractal dimension should be between 1.0 and 3.0, got {result}"


def test_fractal_dim_handles_uniform_image():
    """
    Test that a uniform image (all same pixel values) has a fractal dimension close to 2.0.
    A perfectly uniform 2D surface has a fractal dimension of 2.0.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        mock_path = Path(tmp_dir) / "uniform_fractal_image.png"
        
        # Create a uniform image
        data = np.ones((64, 64), dtype=np.uint8) * 128
        img = Image.fromarray(data, mode='L')
        img.save(mock_path)
        
        result = calculate_fractal_dimension(mock_path)
        
        # Uniform image should have a fractal dimension close to 2.0 (a flat plane)
        assert result >= 1.0, "Fractal dimension cannot be less than 1.0 for a 2D image"
        # Allow some tolerance due to numerical precision and algorithm specifics
        assert result <= 2.1, f"Uniform image fractal dimension should be near 2.0, got {result}"


def test_fractal_dim_nonexistent_file():
    """
    Test that calculate_fractal_dimension raises an appropriate error for a non-existent file.
    """
    mock_path = Path("/tmp/nonexistent_fractal_image_12345.png")
    
    with pytest.raises((FileNotFoundError, ValueError, OSError)):
        calculate_fractal_dimension(mock_path)


def test_hrf_convolve_matches_shape():
    """
    Test that convolve_with_hrf returns an output array with length >= input length.
    This test is designed to fail before the implementation is complete.
    
    The HRF convolution typically increases the length of the time series due to the
    impulse response function's duration.
    """
    # Create a dummy time-series
    # Using a simple sine wave with noise to simulate BOLD-like signal
    np.random.seed(42)
    n_timepoints = 100
    dummy_series = np.sin(np.linspace(0, 4 * np.pi, n_timepoints)) + 0.1 * np.random.randn(n_timepoints)
    
    # Call the function
    output = convolve_with_hrf(dummy_series)
    
    # Assert the output is a numpy array
    assert isinstance(output, np.ndarray), "Output should be a numpy array"
    
    # Assert the output length is at least as long as the input
    # Convolution typically increases length, but at minimum it should not shrink
    assert len(output) >= len(dummy_series), f"Expected output length >= {len(dummy_series)}, got {len(output)}"
    
    # Additional sanity checks
    assert not np.any(np.isnan(output)), "Output should not contain NaN values"
    assert not np.any(np.isinf(output)), "Output should not contain Inf values"
    
    # Verify that the output contains some variance (HRF should not flatten the signal completely)
    assert np.var(output) > 0, "Output should have non-zero variance"