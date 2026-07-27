import os
import tempfile
import shutil
import hashlib
from PIL import Image
import pytest

from utils import sanitize_image_pii, compute_file_checksum

def create_test_image(filepath: str, mode: str = 'RGB', color: tuple = (255, 0, 0)):
    """Helper to create a simple test image."""
    img = Image.new(mode, (100, 100), color=color)
    img.save(filepath, "JPEG")
    return filepath

class TestPIISanitization:
    
    def test_sanitize_renames_to_hash(self, tmp_path):
        """Test that images are renamed to img_<sha256_hash>.jpg"""
        # Setup
        img_dir = tmp_path / "images"
        img_dir.mkdir()
        original_file = img_dir / "original_name.jpg"
        create_test_image(str(original_file))
        
        # Calculate expected hash
        expected_hash = compute_file_checksum(str(original_file))
        expected_new_name = f"img_{expected_hash}.jpg"
        
        # Execute
        count = sanitize_image_pii(str(img_dir))
        
        # Assert
        assert count == 1
        assert (img_dir / expected_new_name).exists()
        assert not (img_dir / "original_name.jpg").exists()

    def test_sanitize_strips_exif(self, tmp_path):
        """Test that EXIF data is removed from images."""
        # Setup
        img_dir = tmp_path / "images"
        img_dir.mkdir()
        original_file = img_dir / "with_exif.jpg"
        
        # Create image with EXIF
        img = Image.new('RGB', (100, 100), color=(0, 255, 0))
        # Add some fake EXIF data (using a dict for simplicity, though PIL usually needs bytes)
        # We'll just save it, then manually ensure the next save strips it.
        img.save(str(original_file), "JPEG", exif=b"fake_exif_data_12345")
        
        # Verify EXIF exists before
        with Image.open(str(original_file)) as img_check:
            # If exif is present, it won't be empty
            assert img_check.info.get('exif') is not None or len(img_check.info) > 0
        
        # Execute
        count = sanitize_image_pii(str(img_dir))
        
        # Find the new file
        new_files = list(img_dir.glob("img_*.jpg"))
        assert len(new_files) == 1
        new_file_path = new_files[0]
        
        # Verify EXIF is gone
        with Image.open(str(new_file_path)) as img_check:
            # After sanitization, exif should be None or empty
            # PIL might not have 'exif' key if stripped
            assert img_check.info.get('exif') is None

    def test_sanitize_handles_mixed_formats(self, tmp_path):
        """Test that sanitization handles PNG and JPEG."""
        img_dir = tmp_path / "images"
        img_dir.mkdir()
        
        jpg_file = img_dir / "test.jpg"
        png_file = img_dir / "test.png"
        
        create_test_image(str(jpg_file), "RGB", (255, 0, 0))
        # PNG
        img_png = Image.new('RGB', (100, 100), color=(0, 0, 255))
        img_png.save(str(png_file), "PNG")
        
        # Execute
        count = sanitize_image_pii(str(img_dir))
        
        # Assert
        assert count == 2
        # Check that original files are gone
        assert not jpg_file.exists()
        assert not png_file.exists()
        # Check that new hash files exist (we don't check exact names here as hashes differ)
        assert len(list(img_dir.glob("img_*.jpg"))) == 2

    def test_sanitize_empty_directory(self, tmp_path):
        """Test that sanitization returns 0 for empty directory."""
        img_dir = tmp_path / "images"
        img_dir.mkdir()
        
        count = sanitize_image_pii(str(img_dir))
        assert count == 0

    def test_sanitize_non_existent_directory(self, tmp_path):
        """Test that sanitization handles non-existent directory gracefully."""
        count = sanitize_image_pii(str(tmp_path / "non_existent"))
        assert count == 0