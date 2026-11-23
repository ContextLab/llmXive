"""
Tests for src.metrics.load_stimuli module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import numpy as np
from PIL import Image

from src.metrics.load_stimuli import (
    StimuliLoaderError,
    get_stimuli_metadata,
    load_stimuli_from_archive
)
from src.lib.utils import compute_file_checksum


@pytest.fixture
def temp_archive_environment():
    """Create a temporary directory structure simulating a valid stimuli archive."""
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = Path(tmpdir)
        
        # Create dummy images and manifest
        filenames = ["img_001.jpg", "img_002.jpg", "img_003.png"]
        manifest_entries = []
        
        for fname in filenames:
            img_path = archive_path / fname
            # Create a simple RGB image
            img = Image.new('RGB', (100, 100), color=(73, 109, 137))
            img.save(img_path)
            
            checksum = compute_file_checksum(img_path)
            manifest_entries.append({
                "filename": fname,
                "sha256": checksum
            })
        
        # Write manifest
        manifest_path = archive_path / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest_entries, f)
            
        yield archive_path, manifest_entries


def test_load_from_archive_success(temp_archive_environment):
    """Test successful loading of images from archive."""
    archive_path, manifest_entries = temp_archive_environment
    
    images, metadata = load_stimuli_from_archive(archive_path)
    
    assert len(images) == len(manifest_entries)
    assert len(metadata) == len(manifest_entries)
    
    for i, meta in enumerate(metadata):
        assert "filename" in meta
        assert "sha256" in meta
        assert meta["filename"] == manifest_entries[i]["filename"]
        assert meta["sha256"] == manifest_entries[i]["sha256"]
        assert images[i].size == (100, 100)


def test_load_with_max_images(temp_archive_environment):
    """Test loading a limited number of images."""
    archive_path, manifest_entries = temp_archive_environment
    
    images, metadata = load_stimuli_from_archive(archive_path, max_images=2)
    
    assert len(images) == 2
    assert len(metadata) == 2


def test_load_missing_archive():
    """Test that missing archive directory raises error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_path = Path(tmpdir) / "non_existent"
        
        with pytest.raises(StimuliLoaderError, match="does not exist"):
            load_stimuli_from_archive(fake_path)


def test_load_missing_manifest(temp_archive_environment):
    """Test that missing manifest file raises error."""
    archive_path, _ = temp_archive_environment
    
    # Remove manifest
    (archive_path / "manifest.json").unlink()
    
    with pytest.raises(StimuliLoaderError, match="Manifest file not found"):
        load_stimuli_from_archive(archive_path)


def test_get_stimuli_metadata(temp_archive_environment):
    """Test metadata extraction from manifest."""
    archive_path, expected_entries = temp_archive_environment
    
    metadata = get_stimuli_metadata(archive_path)
    
    assert len(metadata) == len(expected_entries)
    assert metadata[0]["filename"] == expected_entries[0]["filename"]
    assert metadata[0]["sha256"] == expected_entries[0]["sha256"]


def test_invalid_image_file(temp_archive_environment):
    """Test handling of a corrupted/invalid image file."""
    archive_path, manifest_entries = temp_archive_environment
    
    # Corrupt one image file
      # Corrupt one image file
    corrupt_path = archive_path / manifest_entries[0]["filename"]
    corrupt_path.write_text("not an image")
    
    # Recalculate checksum to match the corrupted content so manifest validation passes checksum-wise
    # but image loading fails
    new_checksum = compute_file_checksum(corrupt_path)
    manifest_entries[0]["sha256"] = new_checksum
    
    # Update manifest
    with open(archive_path / "manifest.json", 'w') as f:
        json.dump(manifest_entries, f)
        
    with pytest.raises(StimuliLoaderError, match="Failed to load image"):
        load_stimuli_from_archive(archive_path)


def test_checksum_mismatch(temp_archive_environment):
    """Test that checksum mismatch raises error."""
    archive_path, manifest_entries = temp_archive_environment
    
    # Modify an image file after checksum was recorded
    img_path = archive_path / manifest_entries[0]["filename"]
    original_content = img_path.read_bytes()
    
    # Write different content
    img_path.write_bytes(b"corrupted content")
    
    # Manifest still has old checksum
    with pytest.raises(StimuliLoaderError, match="Checksum mismatch"):
        load_stimuli_from_archive(archive_path)
        
    # Restore (though temp dir will be cleaned up anyway)
    img_path.write_bytes(original_content)
