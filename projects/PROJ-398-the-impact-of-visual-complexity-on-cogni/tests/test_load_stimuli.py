"""
Tests for src/metrics/load_stimuli.py
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import numpy as np
from PIL import Image

from src.metrics.load_stimuli import (
    load_stimuli_from_archive,
    get_stimuli_metadata,
    StimuliLoaderError
)
from src.lib.utils import compute_file_checksum

@pytest.fixture
def temp_archive_environment():
    """Create a temporary directory with valid stimuli and manifest."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create dummy images
        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.jpg"
        
        img1 = Image.new('RGB', (100, 100), color='red')
        img1.save(img1_path)
        
        img2 = Image.new('RGB', (100, 100), color='blue')
        img2.save(img2_path)
        
        # Calculate checksums
        checksum1 = compute_file_checksum(img1_path)
        checksum2 = compute_file_checksum(img2_path)
        
        # Create manifest
        manifest = {
            "img1.png": checksum1,
            "img2.jpg": checksum2,
            "readme.txt": "dummy" # Non-image file to be ignored
        }
        
        manifest_path = tmp_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)
            
        yield tmp_path

def test_load_from_archive_success(temp_archive_environment):
    """Test successful loading of stimuli from a valid archive."""
    data = load_stimuli_from_archive(temp_archive_environment)
    
    assert len(data) == 2
    filenames = [item[0] for item in data]
    assert "img1.png" in filenames
    assert "img2.jpg" in filenames
    
    # Check image data
    for fname, array, checksum in data:
        assert isinstance(array, np.ndarray)
        assert array.shape == (100, 100, 3)
        assert len(checksum) == 64 # SHA-256 hex length

def test_load_with_max_images(temp_archive_environment):
    """Test loading with a limit on the number of images."""
    data = load_stimuli_from_archive(temp_archive_environment, max_images=1)
    
    assert len(data) == 1
    # Verify ordering is deterministic (sorted)
    assert data[0][0] == "img1.png"

def test_load_missing_archive():
    """Test that loading from a non-existent directory raises an error."""
    with pytest.raises(StimuliLoaderError) as exc_info:
        load_stimuli_from_archive(Path("/nonexistent/path"))
    assert "Archive directory does not exist" in str(exc_info.value)

def test_load_missing_manifest(temp_archive_environment):
    """Test that loading without a manifest raises an error."""
    # Remove manifest
    manifest_path = temp_archive_environment / "manifest.json"
    manifest_path.unlink()
    
    with pytest.raises(StimuliLoaderError) as exc_info:
        load_stimuli_from_archive(temp_archive_environment)
    assert "Manifest file not found" in str(exc_info.value)

def test_get_stimuli_metadata(temp_archive_environment):
    """Test extracting metadata from manifest."""
    meta = get_stimuli_metadata(temp_archive_environment)
    assert "img1.png" in meta
    assert "img2.jpg" in meta
    assert "readme.txt" in meta # Manifest contains it, filtering happens in loader

def test_invalid_image_file(temp_archive_environment):
    """Test handling of a file that is in manifest but not a valid image."""
    # Add a dummy file to manifest but not create it
    manifest_path = temp_archive_environment / "manifest.json"
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    manifest["fake_image.png"] = "0" * 64 # Fake checksum
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)
        
    with pytest.raises(StimuliLoaderError) as exc_info:
        load_stimuli_from_archive(temp_archive_environment)
    assert "Stimulus file missing" in str(exc_info.value)

def test_checksum_mismatch(temp_archive_environment):
    """Test that a checksum mismatch raises an error."""
    # Corrupt the checksum in the manifest
    manifest_path = temp_archive_environment / "manifest.json"
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    manifest["img1.png"] = "0" * 64 # Wrong checksum
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)
        
    with pytest.raises(StimuliLoaderError) as exc_info:
        load_stimuli_from_archive(temp_archive_environment)
    assert "Checksum mismatch" in str(exc_info.value)