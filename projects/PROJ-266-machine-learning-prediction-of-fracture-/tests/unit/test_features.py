"""
Unit tests for texture feature extraction.
"""
import pytest
import numpy as np
from pathlib import Path
import json
import tempfile
from PIL import Image

# Import functions to test
from code.data.features import compute_glcm_features, compute_band_pass_spectrum, extract_features_from_image, run_feature_extraction

@pytest.fixture
def sample_image(tmp_path):
    """Create a temporary sample image for testing."""
    img = Image.new('L', (64, 64), color=128)
    # Add some pattern
    for i in range(64):
        for j in range(64):
            if (i + j) % 2 == 0:
                img.putpixel((i, j), 200)
            else:
                img.putpixel((i, j), 50)
    
    img_path = tmp_path / "test_image.png"
    img.save(img_path)
    return img_path

def test_glcm_features_structure(sample_image):
    """Test that GLCM features return a dictionary with expected keys."""
    img_array = np.array(Image.open(sample_image))
    features = compute_glcm_features(img_array)
    
    assert isinstance(features, dict)
    assert len(features) > 0
    # Check for at least one feature type
    assert any("contrast" in k for k in features.keys())
    assert any("energy" in k for k in features.keys())

def test_band_pass_spectrum_structure(sample_image):
    """Test that band-pass spectrum returns a list of numbers."""
    img_array = np.array(Image.open(sample_image))
    spectrum = compute_band_pass_spectrum(img_array)
    
    assert isinstance(spectrum, list)
    assert len(spectrum) > 0
    assert all(isinstance(v, (int, float)) for v in spectrum)

def test_extract_features_from_image(sample_image):
    """Test full feature extraction pipeline on a single image."""
    features = extract_features_from_image(sample_image)
    
    assert isinstance(features, dict)
    assert 'band_pass_spectrum' in features
    assert isinstance(features['band_pass_spectrum'], list)
    assert len(features['band_pass_spectrum']) > 0
    assert 'mean_intensity' in features
    assert 'std_intensity' in features

def test_run_feature_extraction(sample_image, tmp_path):
    """Test batch feature extraction and JSON output."""
    output_file = tmp_path / "features.json"
    
    # Run extraction
    run_feature_extraction(sample_image.parent, output_file)
    
    # Verify output file exists
    assert output_file.exists()
    
    # Verify content
    with open(output_file) as f:
        data = json.load(f)
    
    assert isinstance(data, dict)
    assert str(sample_image.name) in data
    assert 'band_pass_spectrum' in data[str(sample_image.name)]
    assert len(data[str(sample_image.name)]['band_pass_spectrum']) > 0