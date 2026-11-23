"""
Unit tests for stiffness tensor calculation.
"""
import numpy as np
import pytest
from pathlib import Path
from skimage import io
import tempfile
import json

from code.data_generation.compute_stiffness import load_microstructure, compute_stiffness_tensor

def test_load_microstructure_grayscale():
    """Test loading a grayscale microstructure image."""
    # Create a temporary binary image
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        # Create a simple binary image: 50% inclusions
        img = np.zeros((128, 128), dtype=np.uint8)
        img[64:, :] = 255  # Bottom half is inclusion
        io.imsave(tmp.name, img)
        
        loaded = load_microstructure(Path(tmp.name))
        
        assert loaded.shape == (128, 128)
        assert loaded.dtype == np.float32
        # Check that bottom half is 1.0 and top half is 0.0
        assert np.allclose(loaded[64:, :], 1.0)
        assert np.allclose(loaded[:64, :], 0.0)
        
        Path(tmp.name).unlink()

def test_load_microstructure_rgb():
    """Test loading an RGB microstructure image."""
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        # Create a simple RGB binary image
        img = np.zeros((128, 128, 3), dtype=np.uint8)
        img[64:, :] = [255, 255, 255]  # Bottom half is inclusion
        io.imsave(tmp.name, img)
        
        loaded = load_microstructure(Path(tmp.name))
        
        assert loaded.shape == (128, 128)
        assert loaded.dtype == np.float32
        assert np.allclose(loaded[64:, :], 1.0)
        assert np.allclose(loaded[:64, :], 0.0)
        
        Path(tmp.name).unlink()

def test_load_microstructure_not_found():
    """Test that FileNotFoundError is raised for missing image."""
    with pytest.raises(FileNotFoundError):
        load_microstructure(Path("nonexistent_image.png"))

def test_compute_stiffness_tensor_physical_bounds():
    """Test that computed stiffness is within physical bounds."""
    # Create a uniform inclusion image (should be close to inclusion stiffness)
    image = np.ones((128, 128), dtype=np.float32)
    stiffness = compute_stiffness_tensor(image, inclusion_stiffness=200.0, void_stiffness=0.01)
    
    # For uniform inclusion, stiffness should be close to inclusion stiffness
    # (allowing for some numerical error in FFT solver)
    assert stiffness.shape == (4, 4)
    assert stiffness[0, 0] > 0  # Positive stiffness
    assert stiffness[0, 0] < 250.0  # Reasonable upper bound
    
    # Check symmetry
    assert np.allclose(stiffness, stiffness.T)

def test_compute_stiffness_tensor_void():
    """Test that void-only image has very low stiffness."""
    # Create a uniform void image
    image = np.zeros((128, 128), dtype=np.float32)
    stiffness = compute_stiffness_tensor(image, inclusion_stiffness=200.0, void_stiffness=0.01)
    
    # For uniform void, stiffness should be close to void stiffness
    assert stiffness.shape == (4, 4)
    assert stiffness[0, 0] > 0
    assert stiffness[0, 0] < 1.0  # Should be very low

def test_compute_stiffness_tensor_mixed():
    """Test stiffness calculation for mixed microstructure."""
    # Create a checkerboard pattern
    image = np.zeros((128, 128), dtype=np.float32)
    image[::2, ::2] = 1.0  # Checkerboard pattern
    image[1::2, 1::2] = 1.0
    
    stiffness = compute_stiffness_tensor(image, inclusion_stiffness=200.0, void_stiffness=0.01)
    
    assert stiffness.shape == (4, 4)
    assert stiffness[0, 0] > 0
    # Should be between void and inclusion stiffness
    assert stiffness[0, 0] > 0.01
    assert stiffness[0, 0] < 200.0