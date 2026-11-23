import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing.features import (
    compute_gabor_kernel,
    compute_target_salience,
    compute_fixation_count,
    compute_search_time,
    extract_features,
    process_dataset_features
)

@pytest.fixture
def mock_eye_data():
    """Create mock eye-tracking data with x, y columns."""
    data = {
        'timestamp': range(100),
        'x': np.random.randn(100) * 10,
        'y': np.random.randn(100) * 10,
        'pupil_diameter': np.random.randn(100) * 0.5 + 4.0
    }
    return pd.DataFrame(data)

@pytest.fixture
def mock_metadata():
    """Create mock trial metadata."""
    return {
        'search_time': 2.5,
        'target_salience': 0.8
    }

@pytest.fixture
def mock_image(tmp_path):
    """Create a temporary dummy image."""
    img_path = tmp_path / "test_stimulus.png"
    # Create a simple PPM or PNG file
    from PIL import Image
    img = Image.new('L', (32, 32), 128)
    img.save(img_path)
    return img_path

def test_compute_gabor_kernel():
    """Test that Gabor kernel is computed and normalized."""
    kernel = compute_gabor_kernel(orientation=0.0, scale=1.0, size=31)
    assert kernel.shape == (31, 31)
    assert np.abs(kernel).sum() == pytest.approx(1.0, rel=1e-3)
    assert not np.isnan(kernel).any()

def test_compute_target_salience(mock_image):
    """Test salience computation on a dummy image."""
    salience = compute_target_salience(mock_image)
    assert isinstance(salience, float)
    assert salience >= 0.0

def test_compute_target_salience_missing_file(tmp_path):
    """Test that missing image raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        compute_target_salience(tmp_path / "nonexistent.png")

def test_compute_fixation_count(mock_eye_data):
    """Test fixation count on mock data."""
    count = compute_fixation_count(mock_eye_data)
    assert isinstance(count, int)
    assert count >= 0

def test_compute_search_time(mock_metadata):
    """Test search time extraction."""
    time = compute_search_time(mock_metadata)
    assert time == 2.5

def test_compute_search_time_missing_key():
    """Test search time with missing key."""
    with pytest.raises(KeyError):
        compute_search_time({'other_key': 1.0})

def test_extract_features_unfulfillable_salience(mock_eye_data, mock_metadata, tmp_path):
    """Test extraction when salience is unfulfillable (no image, no metadata)."""
    # Remove salience from metadata
    meta_no_sal = {k: v for k, v in mock_metadata.items() if k != 'target_salience'}
    
    feat = extract_features(
        subject_id="S01",
        trial_id="T01",
        eye_data=mock_eye_data,
        trial_metadata=meta_no_sal,
        stimulus_path=tmp_path / "missing.png", # Non-existent
        config={}
    )
    
    assert feat['status'] == 'UNFULFILLABLE'
    assert feat['target_salience'] is None
    assert feat['search_time'] == 2.5
    assert feat['fixation_count'] >= 0

def test_extract_features_ok(mock_eye_data, mock_metadata, mock_image):
    """Test extraction when all data is present."""
    feat = extract_features(
        subject_id="S01",
        trial_id="T01",
        eye_data=mock_eye_data,
        trial_metadata=mock_metadata,
        stimulus_path=mock_image,
        config={}
    )
    
    assert feat['status'] == 'OK'
    assert feat['target_salience'] is not None
    assert feat['search_time'] == 2.5
    assert feat['fixation_count'] >= 0
