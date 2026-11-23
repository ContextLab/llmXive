import pytest
import tempfile
import os
from pathlib import Path
from PIL import Image
import numpy as np

from stimuli.manipulator import add_minor_objects, remove_minor_elements, process_single_image
from utils.logging import setup_logging, get_manipulation_error_log_path

@pytest.fixture
def sample_image():
    """Create a 512x512 RGB sample image."""
    img = Image.new('RGB', (512, 512), color=(128, 128, 128))
    draw = ImageDraw.Draw(img)
    # Add some simple shapes to simulate detail
    draw.rectangle([100, 100, 200, 200], fill=(255, 0, 0))
    draw.rectangle([300, 300, 400, 400], fill=(0, 255, 0))
    return img

@pytest.fixture
def asset_dir(tmp_path):
    """Create a temporary directory with minor object assets."""
    asset_path = tmp_path / "minor_objects"
    asset_path.mkdir()
    
    # Create a few simple PNG assets with transparency
    for i, color in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255)]):
        asset = Image.new('RGBA', (50, 50), color=color + (128,)) # Semi-transparent
        asset.save(asset_path / f"object_{i}.png")
        
    return asset_path

def test_add_minor_objects_creates_output(sample_image, asset_dir):
    """Test that add_minor_objects produces an image with assets overlaid."""
    result = add_minor_objects(sample_image, asset_dir, seed=42)
    
    assert result.size == sample_image.size
    assert result.mode == 'RGB'
    
    # Check that the image is not identical to the original
    orig_arr = np.array(sample_image)
    res_arr = np.array(result)
    assert not np.array_equal(orig_arr, res_arr), "Output should differ from input"

def test_remove_minor_elements_reduces_detail(sample_image):
    """Test that remove_minor_elements reduces local variance."""
    result = remove_minor_elements(sample_image)
    
    assert result.size == sample_image.size
    assert result.mode == 'RGB'
    
    # Convert to numpy arrays
    orig_arr = np.array(sample_image).astype(float)
    res_arr = np.array(result).astype(float)
    
    # Calculate local variance in a region
    region = (100, 100, 200, 200)
    orig_region = orig_arr[region[1]:region[3], region[0]:region[2]]
    res_region = res_arr[region[1]:region[3], region[0]:region[2]]
    
    orig_std = np.std(orig_region)
    res_std = np.std(res_region)
    
    # The blurred region should have lower standard deviation
    # Note: This is a heuristic check; exact thresholds may vary
    assert res_std < orig_std, "Blurred region should have lower variance"

def test_process_single_image_writes_file(sample_image, asset_dir, tmp_path):
    """Test that process_single_image writes a file to disk."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()
    
    # Save sample image
    input_file = input_dir / "test.png"
    sample_image.save(input_file)
    
    # Process
    result_path = process_single_image(input_file, output_dir, asset_dir, mode='enhanced')
    
    assert result_path is not None
    assert result_path.exists()
    assert result_path.name.endswith("_enhanced.png")

def test_process_single_image_handles_missing_assets(tmp_path):
    """Test that process_single_image fails gracefully when assets are missing."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    asset_dir = tmp_path / "missing_assets"
    input_dir.mkdir()
    output_dir.mkdir()
    
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color=(128, 128, 128))
    input_file = input_dir / "test.png"
    img.save(input_file)
    
    # Process should return None and log error
    result_path = process_single_image(input_file, output_dir, asset_dir, mode='enhanced')
    
    assert result_path is None
    # Check that error was logged (side effect)
    log_path = get_manipulation_error_log_path()
    assert log_path.exists()

def test_remove_minor_elements_global_blur(sample_image):
    """Test global blur mode of remove_minor_elements."""
    result = remove_minor_elements(sample_image)
    
    assert result.size == sample_image.size
    # Check that the image is smoother (lower high-frequency content)
    orig_arr = np.array(sample_image)
    res_arr = np.array(result)
    
    # Simple check: mean absolute difference should be non-zero but not huge
    diff = np.abs(orig_arr.astype(float) - res_arr.astype(float))
    assert np.mean(diff) > 0, "Blurred image should differ from original"
    assert np.mean(diff) < 50, "Blurring should not drastically change pixel values"