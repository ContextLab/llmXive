import numpy as np
import pytest
from code.morphometry import skeletonize_and_count, denoise_and_subtract

class TestSkeletonizeAndCount:
    """Unit tests for T014: skeletonization and branch point counting."""

    def test_empty_image_raises_error(self):
        """Test that empty image raises ValueError."""
        with pytest.raises(ValueError):
            skeletonize_and_count(np.array([]))

    def test_no_foreground_returns_zero_branches(self):
        """Test image with no foreground pixels."""
        image = np.zeros((10, 10), dtype=np.uint8)
        skel, count = skeletonize_and_count(image)
        assert count == 0
        assert skel.shape == image.shape
        assert not np.any(skel)

    def test_single_line_no_branches(self):
        """Test a simple horizontal line (0 branches)."""
        image = np.zeros((10, 10), dtype=np.uint8)
        image[5, :] = 255
        skel, count = skeletonize_and_count(image)
        # A straight line should have 0 branch points (junctions)
        assert count == 0

    def test_simple_cross_two_branches(self):
        """Test a cross shape (1 junction -> 1 branch point)."""
        image = np.zeros((10, 10), dtype=np.uint8)
        image[5, :] = 255  # Horizontal
        image[:, 5] = 255  # Vertical
        skel, count = skeletonize_and_count(image)
        # A perfect cross has 1 junction point in the center
        assert count == 1

    def test_complex_tree_multiple_branches(self):
        """Test a tree-like structure with multiple branches."""
        image = np.zeros((20, 20), dtype=np.uint8)
        # Main trunk
        image[10, 5:15] = 255
        # Branch 1
        image[5:10, 10] = 255
        # Branch 2
        image[10:15, 10] = 255
        # Branch 3
        image[10, 10:15] = 255 # Overlapping with trunk, creates a junction
        
        skel, count = skeletonize_and_count(image)
        # This structure has at least 1 junction at (10, 10)
        assert count >= 1

    def test_denoise_and_subtract_integration(self):
        """Test T014 consuming output of T013 (denoise_and_subtract)."""
        # Create a noisy image
        np.random.seed(42)
        noisy_image = np.random.rand(50, 50) * 255
        # Add a clear structure
        noisy_image[20:30, 20:30] = 255
        
        # T013
        binary = denoise_and_subtract(noisy_image)
        
        # T014
        skel, count = skeletonize_and_count(binary)
        
        # Should not crash and should produce a skeleton
        assert skel.shape == binary.shape
        # The count should be non-negative
        assert count >= 0

    def test_boolean_input(self):
        """Test that boolean input is handled correctly."""
        image = np.zeros((10, 10), dtype=bool)
        image[5, :] = True
        skel, count = skeletonize_and_count(image)
        assert count == 0

    def test_8bit_input(self):
        """Test that 8-bit input is handled correctly."""
        image = np.zeros((10, 10), dtype=np.uint8)
        image[5, :] = 128
        skel, count = skeletonize_and_count(image)
        assert count == 0

    def test_large_image_performance(self):
        """Test performance on a larger image."""
        image = np.random.rand(200, 200) > 0.9
        skel, count = skeletonize_and_count(image)
        assert skel.shape == (200, 200)
        assert count >= 0
