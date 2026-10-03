"""
Unit tests for the image loader generator module.

Tests verify that:
1. Generator yields images correctly
2. Memory-efficient processing works
3. Error handling for corrupted files
4. Batch processing functionality
"""
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np
import cv2

# Import the module under test
from image_loader import load_image_generator, batch_image_loader


@pytest.fixture
def temp_image_dir():
    """Create a temporary directory with test images."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create valid test images
        for i in range(5):
            img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            cv2.imwrite(str(tmpdir_path / f"test_{i}.png"), img)
        
        # Create a corrupted file (empty file)
        (tmpdir_path / "corrupted.png").touch()
        
        yield tmpdir_path


def test_generator_yields_images(temp_image_dir):
    """Test that the generator yields all valid images."""
    images = list(load_image_generator(temp_image_dir))
    
    assert len(images) == 5, f"Expected 5 images, got {len(images)}"
    
    for path, img in images:
        assert isinstance(path, Path)
        assert isinstance(img, np.ndarray)
        assert img.shape == (100, 100, 3)


def test_generator_handles_corrupted_files(temp_image_dir):
    """Test that the generator skips corrupted files without crashing."""
    # The generator should skip the corrupted.png file
    images = list(load_image_generator(temp_image_dir))
    
    # Should have 5 valid images, not 6
    assert len(images) == 5
    
    # Verify no corrupted file was yielded
    for path, _ in images:
        assert "corrupted" not in path.name


def test_generator_raises_on_missing_dir():
    """Test that generator raises FileNotFoundError for missing directory."""
    with pytest.raises(FileNotFoundError):
        list(load_image_generator(Path("/nonexistent/path")))


def test_generator_raises_on_no_images():
    """Test that generator raises ValueError when no images found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError):
            list(load_image_generator(Path(tmpdir)))


def test_batch_loader_yields_batches(temp_image_dir):
    """Test that batch loader yields correct batch sizes."""
    batches = list(batch_image_loader(temp_image_dir, batch_size=2))
    
    # Should have 3 batches: 2, 2, 1
    assert len(batches) == 3
    assert len(batches[0]) == 2
    assert len(batches[1]) == 2
    assert len(batches[2]) == 1


def test_batch_loader_batch_size_one(temp_image_dir):
    """Test batch loader with batch_size=1."""
    batches = list(batch_image_loader(temp_image_dir, batch_size=1))
    
    assert len(batches) == 5
    for batch in batches:
        assert len(batch) == 1


def test_generator_memory_efficiency():
    """
    Test that generator processes images one at a time.
    
    This is verified by checking that we can iterate without
    loading all images into a list first.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create 10 small test images
        for i in range(10):
            img = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
            cv2.imwrite(str(tmpdir_path / f"test_{i}.png"), img)
        
        # Process using generator without storing all in memory
        count = 0
        for path, img in load_image_generator(tmpdir_path):
            count += 1
            # Process immediately and discard
            assert img is not None
        
        assert count == 10