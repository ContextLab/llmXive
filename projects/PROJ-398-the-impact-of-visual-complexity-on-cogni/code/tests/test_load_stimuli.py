"""
Tests for the load_stimuli module.
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
    StimuliLoaderError,
    _get_stimuli_archive_path,
    _get_checksum_manifest_path
)
from src.config import PROJECT_ROOT, DATA_DIR


@pytest.fixture
def temp_archive_environment():
    """Create a temporary archive environment for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create archive structure
        archive_path = tmpdir_path / DATA_DIR / "stimuli" / "raw"
        archive_path.mkdir(parents=True)
        
        # Create dummy images
        image_files = []
        for i in range(3):
            img_path = archive_path / f"stimulus_{i:03d}.png"
            img = Image.new('RGB', (640, 360), color=(i*50, i*50, i*50))
            img.save(img_path)
            image_files.append(img_path)
        
        # Create checksum manifest
        manifest = {}
        for img_path in image_files:
            # Compute simple checksum (for testing)
            checksum = hashlib.sha256(img_path.read_bytes()).hexdigest()
            manifest[img_path.name] = checksum
        
        manifest_path = archive_path / "checksums.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)
        
        yield tmpdir_path, archive_path, manifest


def test_load_from_archive_success(temp_archive_environment):
    """Test that stimuli are loaded successfully from a valid archive."""
    tmpdir_path, archive_path, manifest = temp_archive_environment
    
    # Patch the archive path function
    with patch('src.metrics.load_stimuli._get_stimuli_archive_path', return_value=archive_path):
        with patch('src.metrics.load_stimuli._get_checksum_manifest_path', return_value=archive_path / "checksums.json"):
            stimuli = load_stimuli_from_archive()
            
            assert len(stimuli) == 3
            assert all('image_id' in s for s in stimuli)
            assert all('path' in s for s in stimuli)
            assert all('pil_image' in s for s in stimuli)
            assert all('checksum' in s for s in stimuli)
            
            # Verify images are loaded correctly
            for stim in stimuli:
                assert isinstance(stim['pil_image'], Image.Image)
                assert stim['pil_image'].size == (640, 360)


def test_load_with_max_images(temp_archive_environment):
    """Test that max_images parameter limits the number of loaded stimuli."""
    tmpdir_path, archive_path, manifest = temp_archive_environment
    
    with patch('src.metrics.load_stimuli._get_stimuli_archive_path', return_value=archive_path):
        with patch('src.metrics.load_stimuli._get_checksum_manifest_path', return_value=archive_path / "checksums.json"):
            stimuli = load_stimuli_from_archive(max_images=2)
            
            assert len(stimuli) == 2


def test_load_missing_archive():
    """Test that loading fails when archive is missing."""
    with patch('src.metrics.load_stimuli._get_stimuli_archive_path', return_value=Path('/nonexistent/path')):
        with pytest.raises(StimuliLoaderError, match="Stimuli archive not found"):
            load_stimuli_from_archive()


def test_load_missing_manifest():
    """Test that loading fails when manifest is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = Path(tmpdir) / DATA_DIR / "stimuli" / "raw"
        archive_path.mkdir(parents=True)
        
        # Create a dummy image but no manifest
        img = Image.new('RGB', (640, 360))
        img.save(archive_path / "dummy.png")
        
        with patch('src.metrics.load_stimuli._get_stimuli_archive_path', return_value=archive_path):
            with patch('src.metrics.load_stimuli._get_checksum_manifest_path', return_value=archive_path / "checksums.json"):
                with pytest.raises(StimuliLoaderError, match="Checksum manifest not found"):
                    load_stimuli_from_archive()


def test_get_stimuli_metadata(temp_archive_environment):
    """Test metadata retrieval without loading full images."""
    tmpdir_path, archive_path, manifest = temp_archive_environment
    
    with patch('src.metrics.load_stimuli._get_stimuli_archive_path', return_value=archive_path):
        with patch('src.metrics.load_stimuli._get_checksum_manifest_path', return_value=archive_path / "checksums.json"):
            metadata = get_stimuli_metadata()
            
            assert len(metadata) == 3
            assert all('image_id' in m for m in metadata)
            assert all('path' in m for m in metadata)
            assert all('checksum' in m for m in metadata)
            assert all('size_bytes' in m for m in metadata)
            
            # Verify no PIL images are loaded
            for m in metadata:
                assert 'pil_image' not in m


def test_invalid_image_file():
    """Test that invalid image files are detected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = Path(tmpdir) / DATA_DIR / "stimuli" / "raw"
        archive_path.mkdir(parents=True)
        
        # Create a non-image file
        dummy_file = archive_path / "invalid.png"
        dummy_file.write_text("not an image")
        
        # Create manifest
        manifest = {
            "invalid.png": "dummy_checksum"
        }
        manifest_path = archive_path / "checksums.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)
        
        with patch('src.metrics.load_stimuli._get_stimuli_archive_path', return_value=archive_path):
            with patch('src.metrics.load_stimuli._get_checksum_manifest_path', return_value=manifest_path):
                with patch('src.metrics.load_stimuli.verify_archive_integrity', return_value=(True, None)):
                    with pytest.raises(StimuliLoaderError, match="Invalid image file"):
                        load_stimuli_from_archive()


def test_checksum_mismatch():
    """Test that checksum mismatches are detected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = Path(tmpdir) / DATA_DIR / "stimuli" / "raw"
        archive_path.mkdir(parents=True)
        
        # Create a valid image
        img = Image.new('RGB', (640, 360))
        img_path = archive_path / "valid.png"
        img.save(img_path)
        
        # Create manifest with wrong checksum
        manifest = {
            "valid.png": "wrong_checksum_123456789012345678901234567890123456789012345678901234567890"
        }
        manifest_path = archive_path / "checksums.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f)
        
        with patch('src.metrics.load_stimuli._get_stimuli_archive_path', return_value=archive_path):
            with patch('src.metrics.load_stimuli._get_checksum_manifest_path', return_value=manifest_path):
                with patch('src.metrics.load_stimuli.verify_archive_integrity', return_value=(True, None)):
                    with pytest.raises(StimuliLoaderError, match="Checksum mismatch"):
                        load_stimuli_from_archive()