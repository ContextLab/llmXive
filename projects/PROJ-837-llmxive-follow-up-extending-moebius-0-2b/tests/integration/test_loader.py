"""
Integration tests for code/data/loader.py
Tests T012: Fetch Places365 subset from HuggingFace with checksum verification.
"""
import os
import json
import tempfile
from pathlib import Path
import hashlib

import pytest
from PIL import Image
import numpy as np

# Import the module under test
# We need to add the project root to sys.path for imports to work
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data import loader
from code.config import is_ci_mode
from code.config_env import get_datasets_path, reset_env_config

class TestPlaces365Loader:
    """Integration tests for Places365 dataset loading."""

    def test_download_and_cache_dataset_exists(self):
        """Test that the dataset is downloaded and cached correctly."""
        # This test will actually attempt to download a small subset
        # In CI mode, we limit the size to keep it fast
        max_samples = 5 if is_ci_mode() else 20
        
        dataset_dir, metadata = loader.download_and_cache_dataset(
            split="train",
            max_samples=max_samples
        )
        
        assert dataset_dir.exists(), f"Dataset directory not created: {dataset_dir}"
        assert len(metadata) > 0, "No images were processed"
        assert len(metadata) <= max_samples, f"Too many images: {len(metadata)} > {max_samples}"
        
        # Check metadata file exists
        meta_file = dataset_dir / "metadata.json"
        assert meta_file.exists(), "Metadata file not created"
        
        # Verify metadata structure
        with open(meta_file) as f:
            loaded_meta = json.load(f)
        
        assert len(loaded_meta) == len(metadata), "Metadata count mismatch"
        
        # Check required fields in metadata
        required_fields = ["image_id", "filename", "path", "checksum", "width", "height"]
        for item in loaded_meta:
            for field in required_fields:
                assert field in item, f"Missing field {field} in metadata"

    def test_checksum_computation_consistency(self):
        """Test that checksum computation is consistent."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            # Create a simple image
            img = Image.new('RGB', (100, 100), color='red')
            img.save(tmp.name, format='JPEG')
            tmp_path = Path(tmp.name)
        
        try:
            # Compute checksum twice
            hash1 = loader.compute_file_checksum(tmp_path)
            hash2 = loader.compute_file_checksum(tmp_path)
            
            assert hash1 == hash2, "Checksums are not consistent"
            assert len(hash1) == 64, f"Invalid checksum length: {len(hash1)}"
            assert all(c in '0123456789abcdef' for c in hash1), "Invalid checksum format"
        finally:
            tmp_path.unlink()

    def test_verify_checksum_pass(self):
        """Test that verify_checksum returns True for valid file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
            tmp.write(b"test content")
            tmp_path = Path(tmp.name)
        
        try:
            hash_val = loader.compute_file_checksum(tmp_path)
            result = loader.verify_checksum(tmp_path, hash_val)
            assert result is True, "Valid checksum should verify"
        finally:
            tmp_path.unlink()

    def test_verify_checksum_fail(self):
        """Test that verify_checksum returns False for invalid file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
            tmp.write(b"test content")
            tmp_path = Path(tmp.name)
        
        try:
            result = loader.verify_checksum(tmp_path, "invalid_hash_1234567890123456789012345678901234567890123456789012")
            assert result is False, "Invalid checksum should fail"
        finally:
            tmp_path.unlink()

    def test_load_image_function(self):
        """Test that load_image correctly loads an image."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            img = Image.new('RGB', (64, 64), color='blue')
            img.save(tmp.name, format='JPEG')
            tmp_path = Path(tmp.name)
        
        try:
            img_array = loader.load_image(tmp_path)
            
            assert isinstance(img_array, np.ndarray), "Should return numpy array"
            assert img_array.shape == (64, 64, 3), f"Wrong shape: {img_array.shape}"
            assert img_array.dtype == np.uint8, f"Wrong dtype: {img_array.dtype}"
        finally:
            tmp_path.unlink()

    def test_get_image_paths(self):
        """Test that get_image_paths returns correct list."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Create some dummy image files
            (tmp_path / "img1.jpg").touch()
            (tmp_path / "img2.png").touch()
            (tmp_path / "not_an_image.txt").touch()
            
            paths = loader.get_image_paths(tmp_path)
            
            assert len(paths) == 2, f"Expected 2 images, got {len(paths)}"
            assert all(p.suffix in ['.jpg', '.png'] for p in paths), "Should only return image files"

    def test_full_load_dataset_for_training(self):
        """Test the main entry point load_dataset_for_training."""
        max_samples = 5 if is_ci_mode() else 20
        
        dataset_dir, metadata = loader.load_dataset_for_training(
            split="train",
            max_samples=max_samples
        )
        
        assert dataset_dir.exists(), "Dataset directory should exist"
        assert len(metadata) > 0, "Should have loaded images"
        assert len(metadata) <= max_samples, "Should respect max_samples limit"
        
        # Verify all paths in metadata exist
        for item in metadata:
            path = Path(item["path"])
            assert path.exists(), f"Image path in metadata does not exist: {path}"
            assert path.parent == dataset_dir, "Image should be in dataset directory"