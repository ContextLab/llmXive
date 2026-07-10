"""
Unit tests for image manipulation logic in stimuli.manipulator.
"""
import pytest
from pathlib import Path
from PIL import Image
import numpy as np
import random

# Import functions from the manipulator module
from stimuli.manipulator import add_minor_objects, remove_minor_elements, calculate_complexity_score

@pytest.fixture
def sample_image():
    """Create a sample RGB image for testing."""
    width, height = 200, 200
    img = Image.new("RGB", (width, height), color=(128, 128, 128))
    return img

@pytest.fixture
def sample_rgba_image():
    """Create a sample RGBA image for testing."""
    width, height = 200, 200
    img = Image.new("RGBA", (width, height), color=(128, 128, 128, 255))
    return img

def test_add_minor_objects_shape(sample_rgba_image):
    """
    Test that add_minor_objects preserves image dimensions and returns correct object count.
    Asserts: output_image.shape == (height, width, 3) and object_count == 5.
    """
    # Create a mock asset pool with a simple programmatically generated asset
    # to avoid dependency on external files during unit tests
    mock_asset = Image.new("RGBA", (20, 20), color=(255, 0, 0, 128))
    
    # Patch the _load_asset function behavior by passing a custom asset list
    # and ensuring our mock asset is used
    num_objects = 5
    
    # Since we can't easily mock the internal _load_asset, we create a test
    # that verifies the logic by checking the output after manual asset injection
    # For this unit test, we simulate the behavior by creating a test asset
    # and directly calling the function with a controlled asset pool.
    
    # To properly test without external files, we create a temporary asset
    # and ensure the function can process it.
    # However, since the function loads from disk, we'll test the shape and count
    # by ensuring the function runs and returns the expected object count.
    
    # Mock asset pool with a single asset we create on the fly
    # Note: In a real test environment, assets should exist in data/stimuli/assets/
    # For this test, we assume the assets exist or skip if not.
    
    # Create a test asset file
    asset_path = Path("data/stimuli/assets/test_asset.png")
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    test_asset = Image.new("RGBA", (20, 20), color=(255, 0, 0, 128))
    test_asset.save(asset_path)
    
    try:
        output_image, object_count = add_minor_objects(
            sample_rgba_image,
            num_objects=num_objects,
            asset_pool=["test_asset.png"],
            max_scale=0.1,
            min_scale=0.05,
        )
        
        # Assert output image shape
        assert output_image.size == sample_rgba_image.size, \
            f"Expected size {sample_rgba_image.size}, got {output_image.size}"
        
        # Convert to array to check shape
        arr = np.array(output_image)
        assert arr.shape == (200, 200, 4), \
            f"Expected shape (200, 200, 4), got {arr.shape}"
        
        # Assert object count
        assert object_count == num_objects, \
            f"Expected {num_objects} objects, got {object_count}"
    
    finally:
        # Cleanup
        if asset_path.exists():
            asset_path.unlink()

def test_remove_minor_elements_variance(sample_rgba_image):
    """
    Test that remove_minor_elements reduces texture variance in masked regions.
    Asserts: output_image has reduced texture variance compared to input.
    """
    # Create an image with high variance (checkerboard pattern)
    width, height = 200, 200
    img_array = np.zeros((height, width), dtype=np.uint8)
    for i in range(0, height, 10):
        for j in range(0, width, 10):
            if (i // 10 + j // 10) % 2 == 0:
                img_array[i:i+10, j:j+10] = 255
            else:
                img_array[i:i+10, j:j+10] = 0
    
    input_img = Image.fromarray(img_array, mode="L").convert("RGBA")
    
    # Apply blur
    output_img = remove_minor_elements(input_img, blur_radius=5, mask_percentage=0.5)
    
    # Calculate variance of input and output (converted to grayscale)
    input_arr = np.array(input_img.convert("L"))
    output_arr = np.array(output_img.convert("L"))
    
    input_variance = np.var(input_arr)
    output_variance = np.var(output_arr)
    
    # Assert reduced variance
    assert output_variance < input_variance, \
        f"Expected reduced variance, got input={input_variance:.2f}, output={output_variance:.2f}"

def test_calculate_complexity_score(sample_image):
    """Test that calculate_complexity_score returns a value between 0 and 1."""
    score = calculate_complexity_score(sample_image)
    assert 0.0 <= score <= 1.0, f"Complexity score {score} out of range [0, 1]"

def test_add_minor_objects_rgb_conversion(sample_image):
    """Test that add_minor_objects correctly handles RGB input images."""
    mock_asset = Image.new("RGBA", (20, 20), color=(255, 0, 0, 128))
    asset_path = Path("data/stimuli/assets/test_asset_rgb.png")
    asset_path.parent.mkdir(parents=True, exist_ok=True)
    mock_asset.save(asset_path)
    
    try:
        output_image, object_count = add_minor_objects(
            sample_image,
            num_objects=3,
            asset_pool=["test_asset_rgb.png"],
            max_scale=0.1,
            min_scale=0.05,
        )
        
        assert output_image.mode == "RGBA", \
            f"Expected RGBA mode, got {output_image.mode}"
        assert object_count == 3, \
            f"Expected 3 objects, got {object_count}"
    finally:
        if asset_path.exists():
            asset_path.unlink()
