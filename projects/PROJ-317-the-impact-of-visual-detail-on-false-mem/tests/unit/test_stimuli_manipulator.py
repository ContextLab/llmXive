"""
Unit tests for the image manipulation logic in code/stimuli/manipulator.py.

Tests both the `add_minor_objects` (enhancement) and `remove_minor_elements` (reduction)
functions to ensure they correctly modify images as expected.
"""
import pytest
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
import sys
import os

# Add the code directory to the path to allow imports from sibling modules
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from stimuli.manipulator import add_minor_objects, remove_minor_elements
from config import get_project_root


def _create_test_image(path: Path, color: tuple = (0, 0, 0), noise: bool = True):
    """Helper to create a deterministic test image."""
    height, width = 100, 100
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    if noise:
        # Add some high-frequency noise to ensure texture variance exists
        arr += np.random.randint(10, 50, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, mode='RGB')
    img.save(path)
    return img


def test_add_minor_objects():
    """
    Test that add_minor_objects correctly overlays minor objects.
    
    Assertions:
    1. output_image.shape == (height, width, 3)
    2. object_count == 5
    """
    project_root = get_project_root()
    test_output_dir = project_root / "data" / "stimuli" / "test_output"
    test_output_dir.mkdir(parents=True, exist_ok=True)
    
    input_path = test_output_dir / "baseline_test_add.png"
    output_path = test_output_dir / "enhanced_test_add.png"
    
    _create_test_image(input_path)
    
    num_objects = 5
    
    output_image, object_count = add_minor_objects(
        str(input_path), 
        str(output_path), 
        num_objects
    )

    # Assertion 1: Check output image shape
    output_array = np.array(output_image)
    expected_shape = (100, 100, 3)
    
    assert output_array.shape == expected_shape, (
        f"Expected output shape {expected_shape}, but got {output_array.shape}."
    )
    
    # Assertion 2: Check object count
    assert object_count == num_objects, (
        f"Expected object_count to be {num_objects}, but got {object_count}."
    )
    
    # Cleanup
    input_path.unlink(missing_ok=True)
    output_path.unlink(missing_ok=True)
    test_output_dir.rmdir()


def test_remove_minor_elements():
    """
    Test that remove_minor_elements reduces texture variance in the masked region.
    
    The function is expected to apply a blur or mask to reduce high-frequency
    details. We assert that the standard deviation (variance proxy) of the 
    processed image is lower than the input image.
    """
    project_root = get_project_root()
    test_output_dir = project_root / "data" / "stimuli" / "test_output"
    test_output_dir.mkdir(parents=True, exist_ok=True)
    
    input_path = test_output_dir / "baseline_test_remove.png"
    output_path = test_output_dir / "reduced_test_remove.png"
    
    # Create an image with significant noise (high texture variance)
    _create_test_image(input_path, noise=True)
    
    input_image = Image.open(input_path)
    input_array = np.array(input_image)
    
    # Calculate initial variance (using standard deviation of flattened array)
    input_std = np.std(input_array)
    
    # Perform reduction
    output_image = remove_minor_elements(
        str(input_path), 
        str(output_path)
    )
    
    output_array = np.array(output_image)
    output_std = np.std(output_array)
    
    # Assertion: Output variance must be strictly less than input variance
    # This confirms that detail (high frequency noise) was removed
    assert output_std < input_std, (
        f"Expected reduced texture variance. Input std: {input_std:.4f}, "
        f"Output std: {output_std:.4f}. The reduction logic did not remove detail."
    )
    
    # Also verify shape is preserved
    assert output_array.shape == input_array.shape, (
        f"Shape changed from {input_array.shape} to {output_array.shape}."
    )
    
    # Cleanup
    input_path.unlink(missing_ok=True)
    output_path.unlink(missing_ok=True)
    try:
        test_output_dir.rmdir()
    except OSError:
        pass # Directory not empty (other tests might have left files)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])