"""
Unit tests for image processing functions in code/preprocess_images.py.

These tests verify:
1. Error handling for corrupted/invalid image files
2. Correctness of skeletonization and branch point detection
"""
import os
import tempfile
import pytest
import numpy as np
from pathlib import Path
from PIL import Image
import logging

# Import the functions being tested
from preprocess_images import (
    load_and_preprocess_image,
    extract_skeleton_metrics,
    validate_metrics
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestLoadImageCorruptedFile:
    """Test handling of corrupted or invalid image files."""
    
    def test_load_image_handles_corrupted_file_returns_error(self):
        """
        Test that loading a corrupted file returns a specific error.
        
        This test creates a file with invalid image data and verifies that
        the load function raises an appropriate exception with a clear message.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file with invalid image data (not a valid image format)
            corrupted_path = Path(tmpdir) / "corrupted_image.jpg"
            with open(corrupted_path, 'wb') as f:
                # Write random bytes that are not a valid JPEG
                f.write(b'GARBAGE_DATA_NOT_A_VALID_IMAGE')
            
            # Attempt to load the corrupted file
            with pytest.raises(Exception) as exc_info:
                load_and_preprocess_image(corrupted_path)
            
            # Verify the exception message contains expected keywords
            error_message = str(exc_info.value).lower()
            assert "corrupted" in error_message or "invalid" in error_message or "cannot" in error_message, \
                f"Expected error message to indicate corruption/invalidity, got: {error_message}"
            
            logger.info(f"Correctly caught error for corrupted file: {exc_info.value}")

    def test_load_image_handles_nonexistent_file_returns_error(self):
        """Test that loading a non-existent file raises an appropriate error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nonexistent_path = Path(tmpdir) / "does_not_exist.png"
            
            with pytest.raises(FileNotFoundError) as exc_info:
                load_and_preprocess_image(nonexistent_path)
            
            assert "does not exist" in str(exc_info.value).lower() or "no such file" in str(exc_info.value).lower()
            logger.info(f"Correctly caught error for non-existent file: {exc_info.value}")

    def test_load_image_handles_empty_file_returns_error(self):
        """Test that loading an empty file raises an appropriate error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_path = Path(tmpdir) / "empty_image.jpg"
            empty_path.touch()  # Create an empty file
            
            with pytest.raises(Exception) as exc_info:
                load_and_preprocess_image(empty_path)
            
            error_message = str(exc_info.value).lower()
            assert "empty" in error_message or "corrupted" in error_message or "invalid" in error_message
            logger.info(f"Correctly caught error for empty file: {exc_info.value}")

class TestSkeletonizeBranchPoints:
    """Test skeletonization and branch point detection."""
    
    def test_skeletonize_returns_valid_branch_points(self):
        """
        Test that skeletonization of a valid root-like structure returns positive branch points.
        
        Creates a synthetic image with a clear branching structure and verifies
        that the extract_skeleton_metrics function correctly identifies branch points.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a synthetic root image with a clear branching structure
            # This is a simple "Y" shape: one main stem splitting into two branches
            img_array = np.zeros((100, 100), dtype=np.uint8)
            
            # Draw main stem (vertical line)
            img_array[20:80, 50] = 255
            
            # Draw left branch (diagonal)
            for i in range(80, 95):
                img_array[i, 50 - (i - 80)] = 255
            
            # Draw right branch (diagonal)
            for i in range(80, 95):
                img_array[i, 50 + (i - 80)] = 255
            
            # Save as a valid image
            test_image_path = Path(tmpdir) / "synthetic_root.png"
            Image.fromarray(img_array).save(test_image_path)
            
            # Load and preprocess the image
            processed_img = load_and_preprocess_image(test_image_path)
            
            # Extract skeleton metrics
            result = extract_skeleton_metrics(processed_img)
            
            # Assertions
            assert result is not None, "Skeleton extraction should return a result"
            assert result.branch_points > 0, f"Expected branch_points > 0, got {result.branch_points}"
            assert result.endpoints >= 2, f"Expected at least 2 endpoints, got {result.endpoints}"
            assert result.total_length > 0, f"Expected total_length > 0, got {result.total_length}"
            
            logger.info(f"Branch points detected: {result.branch_points}")
            logger.info(f"Endpoints detected: {result.endpoints}")
            logger.info(f"Total length: {result.total_length}")

    def test_skeletonize_simple_line_returns_zero_branch_points(self):
        """
        Test that a simple line (no branches) returns zero branch points.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple vertical line
            img_array = np.zeros((100, 100), dtype=np.uint8)
            img_array[20:80, 50] = 255
            
            test_image_path = Path(tmpdir) / "simple_line.png"
            Image.fromarray(img_array).save(test_image_path)
            
            processed_img = load_and_preprocess_image(test_image_path)
            result = extract_skeleton_metrics(processed_img)
            
            assert result.branch_points == 0, f"Expected 0 branch points for simple line, got {result.branch_points}"
            assert result.endpoints == 2, f"Expected 2 endpoints for simple line, got {result.endpoints}"
            logger.info(f"Simple line test passed: {result.branch_points} branch points")

    def test_skeletonize_handles_noisy_image(self):
        """
        Test that skeletonization handles images with some noise gracefully.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a root-like structure with noise
            img_array = np.zeros((100, 100), dtype=np.uint8)
            
            # Draw main stem
            img_array[20:80, 50] = 255
            
            # Add some noise (random pixels)
            np.random.seed(42)
            noise_coords = np.random.randint(0, 100, (20, 2))
            for coord in noise_coords:
                if 0 <= coord[0] < 100 and 0 <= coord[1] < 100:
                    img_array[coord[0], coord[1]] = 255
            
            test_image_path = Path(tmpdir) / "noisy_root.png"
            Image.fromarray(img_array).save(test_image_path)
            
            processed_img = load_and_preprocess_image(test_image_path)
            result = extract_skeleton_metrics(processed_img)
            
            # Should still return valid metrics (might have some spurious branches due to noise)
            assert result.total_length > 0, "Expected positive total length"
            assert result.endpoints >= 2, "Expected at least 2 endpoints"
            logger.info(f"Noisy image test passed: {result.branch_points} branch points, {result.endpoints} endpoints")

class TestMetricsValidation:
    """Test metrics validation logic."""
    
    def test_validate_metrics_returns_true_for_valid_data(self):
        """Test that valid metrics pass validation."""
        from preprocess_images import RSAMetricsResult
        
        valid_metrics = RSAMetricsResult(
            depth=10.5,
            total_length=25.3,
            branch_points=3,
            endpoints=4,
            surface_area=50.2
        )
        
        is_valid, message = validate_metrics(valid_metrics)
        
        assert is_valid, f"Valid metrics should pass validation, but got: {message}"
        
    def test_validate_metrics_returns_false_for_null_depth(self):
        """Test that null depth fails validation."""
        from preprocess_images import RSAMetricsResult
        
        invalid_metrics = RSAMetricsResult(
            depth=None,
            total_length=25.3,
            branch_points=3,
            endpoints=4,
            surface_area=50.2
        )
        
        is_valid, message = validate_metrics(invalid_metrics)
        
        assert not is_valid, "Null depth should fail validation"
        assert "depth" in message.lower(), f"Error message should mention 'depth': {message}"
        
    def test_validate_metrics_returns_false_for_negative_surface_area(self):
        """Test that negative surface area fails validation."""
        from preprocess_images import RSAMetricsResult
        
        invalid_metrics = RSAMetricsResult(
            depth=10.5,
            total_length=25.3,
            branch_points=3,
            endpoints=4,
            surface_area=-5.0
        )
        
        is_valid, message = validate_metrics(invalid_metrics)
        
        assert not is_valid, "Negative surface area should fail validation"
        assert "surface" in message.lower() or "area" in message.lower(), \
            f"Error message should mention 'surface area': {message}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])