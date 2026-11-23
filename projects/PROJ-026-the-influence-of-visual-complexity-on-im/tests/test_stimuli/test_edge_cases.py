"""
Unit tests for edge cases in stimulus processing and validation.
Tests corrupted images, missing files, and invalid data handling.
"""
import os
import tempfile
import pytest
import numpy as np
import cv2
from pathlib import Path

from config import get_project_root, get_data_path
from stimuli.validate import validate_image, validate_batch, get_valid_images, get_invalid_images
from stimuli.metrics import calculate_edge_density, calculate_entropy, calculate_fractal_dim
from stimuli.batch_processor import load_images_batch, process_stimuli_vectorized
import logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestCorruptedImages:
    """Tests for handling corrupted image files."""

    def test_corrupted_file_validation_fails(self):
        """Validate that a corrupted file (not a real image) is rejected."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"This is not a valid image file content")
            temp_path = f.name

        try:
            is_valid, error_msg = validate_image(temp_path)
            assert not is_valid, "Corrupted file should be invalid"
            assert "corrupt" in error_msg.lower() or "cannot" in error_msg.lower() or "decode" in error_msg.lower()
        finally:
            os.unlink(temp_path)

    def test_empty_file_validation_fails(self):
        """Validate that an empty file is rejected."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            # Write nothing
            temp_path = f.name

        try:
            is_valid, error_msg = validate_image(temp_path)
            assert not is_valid, "Empty file should be invalid"
        finally:
            os.unlink(temp_path)

    def test_truncated_image_validation_fails(self):
        """Validate that a truncated image file is rejected."""
        # Create a minimal valid PNG header
        png_header = b'\x89PNG\r\n\x1a\n'
        # Write header and some random bytes, then truncate
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(png_header)
            f.write(b'\x00' * 10)  # Not enough data for a valid image
            temp_path = f.name

        try:
            is_valid, error_msg = validate_image(temp_path)
            assert not is_valid, "Truncated image should be invalid"
        finally:
            os.unlink(temp_path)

    def test_corrupted_image_in_batch(self):
        """Validate that batch processing handles corrupted files gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid image
            valid_img_path = os.path.join(tmpdir, "valid.jpg")
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.imwrite(valid_img_path, img)

            # Create a corrupted image
            corrupted_path = os.path.join(tmpdir, "corrupted.jpg")
            with open(corrupted_path, "wb") as f:
                f.write(b"not an image")

            valid_list, invalid_list = validate_batch(tmpdir)

            assert len(valid_list) == 1, "Should have one valid image"
            assert len(invalid_list) == 1, "Should have one invalid image"
            assert os.path.basename(valid_list[0]) == "valid.jpg"
            assert os.path.basename(invalid_list[0]) == "corrupted.jpg"

class TestMissingData:
    """Tests for handling missing files and directories."""

    def test_validate_missing_file(self):
        """Validate that a missing file returns False."""
        is_valid, error_msg = validate_image("/nonexistent/path/image.jpg")
        assert not is_valid
        assert "not found" in error_msg.lower() or "no such file" in error_msg.lower()

    def test_validate_batch_empty_directory(self):
        """Validate that an empty directory returns empty lists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            valid_list, invalid_list = validate_batch(tmpdir)
            assert len(valid_list) == 0
            assert len(invalid_list) == 0

    def test_validate_batch_missing_directory(self):
        """Validate that a missing directory returns empty lists."""
        valid_list, invalid_list = validate_batch("/nonexistent/directory")
        assert len(valid_list) == 0
        assert len(invalid_list) == 0

class TestMetricEdgeCases:
    """Tests for edge cases in metric calculations."""

    def test_edge_density_on_solid_color(self):
        """Edge density should be 0 for a solid color image."""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:] = [128, 128, 128]  # Solid gray

        density = calculate_edge_density(img)
        assert density == 0.0, "Solid color should have zero edge density"

    def test_entropy_on_solid_color(self):
        """Entropy should be 0 for a solid color image."""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:] = [255, 255, 255]  # Solid white

        entropy_val = calculate_entropy(img)
        assert entropy_val == 0.0, "Solid color should have zero entropy"

    def test_fractal_dim_on_solid_color(self):
        """Fractal dimension should be low for a solid color image."""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:] = [0, 0, 0]  # Solid black

        dim = calculate_fractal_dim(img)
        # Fractal dimension for a solid image should be close to 0 or 1 (line-like)
        # but definitely not high (2 is plane-filling)
        assert dim < 1.5, "Solid color should have low fractal dimension"

    def test_metrics_on_noise_image(self):
        """Noise images should have higher entropy and edge density than solid images."""
        np.random.seed(42)
        noise_img = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        solid_img = np.zeros((100, 100, 3), dtype=np.uint8)
        solid_img[:] = [128, 128, 128]

        noise_entropy = calculate_entropy(noise_img)
        solid_entropy = calculate_entropy(solid_img)
        assert noise_entropy > solid_entropy, "Noise should have higher entropy"

        noise_density = calculate_edge_density(noise_img)
        solid_density = calculate_edge_density(solid_img)
        assert noise_density > solid_density, "Noise should have higher edge density"

    def test_metrics_on_grayscale_conversion(self):
        """Metrics should work on grayscale images."""
        img = np.random.randint(0, 256, (100, 100), dtype=np.uint8)

        # Should not raise an error
        density = calculate_edge_density(img)
        entropy_val = calculate_entropy(img)
        dim = calculate_fractal_dim(img)

        assert density >= 0
        assert entropy_val >= 0
        assert dim >= 0

class TestBatchProcessorEdgeCases:
    """Tests for edge cases in batch processing."""

    def test_load_images_batch_with_corrupted_files(self):
        """Batch loader should skip corrupted files and return valid ones."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create valid image
            valid_path = os.path.join(tmpdir, "valid.jpg")
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.imwrite(valid_path, img)

            # Create corrupted image
            corrupted_path = os.path.join(tmpdir, "corrupted.jpg")
            with open(corrupted_path, "wb") as f:
                f.write(b"not an image")

            images, valid_paths, invalid_paths = load_images_batch(tmpdir)

            assert len(images) == 1
            assert len(valid_paths) == 1
            assert len(invalid_paths) == 1
            assert os.path.basename(valid_paths[0]) == "valid.jpg"

    def test_process_stimuli_vectorized_with_mixed_validity(self):
        """Vectorized processor should handle mixed valid/invalid batches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create valid image
            valid_path = os.path.join(tmpdir, "valid.jpg")
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.imwrite(valid_path, img)

            # Create corrupted image
            corrupted_path = os.path.join(tmpdir, "corrupted.jpg")
            with open(corrupted_path, "wb") as f:
                f.write(b"not an image")

            # This should not crash, just process valid images
            results = process_stimuli_vectorized([valid_path, corrupted_path])

            # Should have results for valid image only
            assert len(results) == 1
            assert "filename" in results[0]
            assert results[0]["filename"] == "valid.jpg"

class TestMissingDataInProcessing:
    """Tests for missing data scenarios in processing pipelines."""

    def test_process_stimuli_batch_with_no_images(self):
        """Process batch should handle empty directories gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # No images in directory
            results = process_stimuli_vectorized([])
            assert len(results) == 0

    def test_metrics_on_zero_dimensional_image(self):
        """Metrics should handle edge case of very small images."""
        # 1x1 image
        img = np.array([[128]], dtype=np.uint8)

        # Should not crash
        density = calculate_edge_density(img)
        entropy_val = calculate_entropy(img)
        dim = calculate_fractal_dim(img)

        assert isinstance(density, (int, float))
        assert isinstance(entropy_val, (int, float))
        assert isinstance(dim, (int, float))