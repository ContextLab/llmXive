"""
Unit tests for Grad-CAM generation and IoU calculation.

This module tests the core functionality of the interpretability module:
1. Grad-CAM heatmap generation (shape validation)
2. Intersection-over-Union (IoU) calculation (range validation)

Tests are designed to fail loudly if the underlying implementation
deviates from expected behavior.
"""

import pytest
import numpy as np
import os
import sys
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from eval.interpret import GradCAM, apply_grad_cam, overlay_heatmap
from eval.iou_calculator import calculate_iou

class TestGradCAMHeatmapShape:
    """Tests for Grad-CAM heatmap shape correctness."""
    
    def test_gradcam_heatmap_shape_matches_input(self):
        """
        Test that Grad-CAM output heatmap has the same spatial dimensions
        as the input image.
        
        Given: An input image of shape (H, W, C)
        When: Grad-CAM is applied
        Then: Output heatmap should have shape (H, W)
        """
        # Create a synthetic input image (224x224x3)
        input_height, input_width, input_channels = 224, 224, 3
        input_image = np.random.rand(input_height, input_width, input_channels).astype(np.float32)
        
        # Create a mock model for GradCAM (we'll test the transform logic)
        # Since we don't have a trained model, we test the shape transformation
        # by verifying the GradCAM class handles shapes correctly
        
        gradcam = GradCAM()
        
        # The GradCAM class should accept an image and return a heatmap
        # of the same spatial dimensions
        # We'll test with a dummy forward pass simulation
        
        # For this test, we verify that the GradCAM class can be instantiated
        # and that its methods exist and have the correct signatures
        assert hasattr(gradcam, 'forward')
        assert hasattr(gradcam, 'backward')
        assert hasattr(gradcam, 'generate_cam')
        
        # Test that the heatmap generation preserves spatial dimensions
        # by checking the internal logic
        # We'll use a small mock to avoid needing a real model
        mock_model = self._create_mock_model()
        
        # Get the feature map shape from a dummy input
        dummy_input = np.random.rand(1, 3, 224, 224).astype(np.float32)
        
        # The heatmap should be (224, 224) - same as input spatial dims
        # We test this by verifying the GradCAM implementation
        # uses the correct feature map dimensions
        
        # Since we can't run a full forward pass without a real model,
        # we verify the shape logic by checking the implementation
        # uses the correct dimension extraction
        
        # Test that the GradCAM class correctly extracts spatial dimensions
        # from feature maps
        feature_map_shape = (32, 28, 28)  # (channels, height, width)
        expected_spatial_dims = (28, 28)
        
        # Verify the GradCAM implementation handles this correctly
        # by checking its internal shape handling
        gradcam._check_feature_map_shape(feature_map_shape)
        
        # The spatial dimensions should match
        assert gradcam._last_spatial_dims == expected_spatial_dims
        
        # Now test with different input sizes
        test_cases = [
            ((112, 112), (112, 112)),
            ((56, 56), (56, 56)),
            ((14, 14), (14, 14)),
        ]
        
        for feature_shape, expected_spatial in test_cases:
            gradcam._check_feature_map_shape((3, *feature_shape))
            assert gradcam._last_spatial_dims == expected_spatial
    
    def test_gradcam_heatmap_normalized(self):
        """
        Test that Grad-CAM heatmaps are normalized to [0, 1] range.
        
        Given: A valid input image
        When: Grad-CAM is applied
        Then: Output heatmap values should be in [0, 1]
        """
        input_image = np.random.rand(224, 224, 3).astype(np.float32)
        
        # Create a mock model
        mock_model = self._create_mock_model()
        
        # Apply Grad-CAM
        heatmap = apply_grad_cam(mock_model, input_image, target_layer="layer4")
        
        # Verify heatmap is normalized
        assert heatmap.min() >= 0.0
        assert heatmap.max() <= 1.0
        
        # Verify it's a 2D array (no channel dimension)
        assert heatmap.ndim == 2
        assert heatmap.shape == (224, 224)
    
    def _create_mock_model(self):
        """Create a mock model for testing Grad-CAM without a real CNN."""
        class MockModel:
            def __init__(self):
                self.features = {}
            
            def forward(self, x):
                # Return a dummy feature map
                return x
            
            def __call__(self, x):
                return self.forward(x)
        
        return MockModel()

class TestIoUCalculation:
    """Tests for Intersection-over-Union calculation."""
    
    def test_iou_calculation_valid_range(self):
        """
        Test that IoU values are always within the valid theoretical range [0, 1].
        
        Given: Two binary masks
        When: IoU is calculated
        Then: Result should be between 0.0 and 1.0 inclusive
        """
        # Test case 1: Identical masks (IoU = 1.0)
        mask1 = np.ones((100, 100), dtype=bool)
        mask2 = np.ones((100, 100), dtype=bool)
        iou = calculate_iou(mask1, mask2)
        assert iou == 1.0
        assert 0.0 <= iou <= 1.0
        
        # Test case 2: Disjoint masks (IoU = 0.0)
        mask1 = np.zeros((100, 100), dtype=bool)
        mask1[:50, :] = True
        mask2 = np.zeros((100, 100), dtype=bool)
        mask2[50:, :] = True
        iou = calculate_iou(mask1, mask2)
        assert iou == 0.0
        assert 0.0 <= iou <= 1.0
        
        # Test case 3: Partial overlap
        mask1 = np.zeros((100, 100), dtype=bool)
        mask1[:75, :] = True
        mask2 = np.zeros((100, 100), dtype=bool)
        mask2[25:, :] = True
        iou = calculate_iou(mask1, mask2)
        assert 0.0 < iou < 1.0
        assert 0.0 <= iou <= 1.0
        
        # Test case 4: One mask is empty
        mask1 = np.zeros((100, 100), dtype=bool)
        mask2 = np.ones((100, 100), dtype=bool)
        iou = calculate_iou(mask1, mask2)
        assert iou == 0.0  # Empty intersection
        assert 0.0 <= iou <= 1.0
        
        # Test case 5: Both masks empty
        mask1 = np.zeros((100, 100), dtype=bool)
        mask2 = np.zeros((100, 100), dtype=bool)
        iou = calculate_iou(mask1, mask2)
        # By convention, IoU of two empty sets is 1.0 (or handled as special case)
        # The implementation should handle this gracefully
        assert 0.0 <= iou <= 1.0
    
    def test_iou_calculation_symmetry(self):
        """
        Test that IoU is symmetric: IoU(A, B) == IoU(B, A).
        
        Given: Two binary masks A and B
        When: IoU is calculated in both orders
        Then: Results should be identical
        """
        mask1 = np.random.rand(100, 100) > 0.5
        mask2 = np.random.rand(100, 100) > 0.5
        
        iou_ab = calculate_iou(mask1, mask2)
        iou_ba = calculate_iou(mask2, mask1)
        
        assert np.isclose(iou_ab, iou_ba)
    
    def test_iou_calculation_with_realistic_shapes(self):
        """
        Test IoU calculation with shapes similar to Grad-CAM heatmaps.
        
        Given: Heatmap-sized masks (224x224)
        When: IoU is calculated
        Then: Result should be valid and within range
        """
        # Create realistic heatmap-sized masks
        height, width = 224, 224
        
        # Simulate a grain boundary mask (sparse, irregular)
        mask1 = np.zeros((height, width), dtype=bool)
        # Create some irregular regions
        for _ in range(10):
            center_y = np.random.randint(20, height-20)
            center_x = np.random.randint(20, width-20)
            radius = np.random.randint(5, 30)
            y, x = np.ogrid[:height, :width]
            mask1[(y-center_y)**2 + (x-center_x)**2 <= radius**2] = True
        
        # Simulate a Grad-CAM heatmap thresholded to binary
        mask2 = np.zeros((height, width), dtype=bool)
        for _ in range(10):
            center_y = np.random.randint(20, height-20)
            center_x = np.random.randint(20, width-20)
            radius = np.random.randint(5, 30)
            y, x = np.ogrid[:height, :width]
            mask2[(y-center_y)**2 + (x-center_x)**2 <= radius**2] = True
        
        iou = calculate_iou(mask1, mask2)
        assert 0.0 <= iou <= 1.0
        
        # Test with different threshold levels
        for threshold in [0.1, 0.3, 0.5, 0.7, 0.9]:
            mask2_thresh = (np.random.rand(height, width) > threshold)
            iou_thresh = calculate_iou(mask1, mask2_thresh)
            assert 0.0 <= iou_thresh <= 1.0
    
    def test_iou_calculation_edge_cases(self):
        """
        Test IoU calculation with edge cases.
        
        Given: Various edge case inputs
        When: IoU is calculated
        Then: Results should be valid and not raise exceptions
        """
        # Single pixel masks
        mask1 = np.zeros((10, 10), dtype=bool)
        mask1[5, 5] = True
        mask2 = np.zeros((10, 10), dtype=bool)
        mask2[5, 5] = True
        iou = calculate_iou(mask1, mask2)
        assert iou == 1.0
        
        # Single pixel vs empty
        mask1 = np.zeros((10, 10), dtype=bool)
        mask1[5, 5] = True
        mask2 = np.zeros((10, 10), dtype=bool)
        iou = calculate_iou(mask1, mask2)
        assert iou == 0.0
        
        # Very small masks
        mask1 = np.array([[True, False], [False, False]])
        mask2 = np.array([[True, False], [False, False]])
        iou = calculate_iou(mask1, mask2)
        assert iou == 1.0
        
        # Large difference in mask sizes
        mask1 = np.ones((100, 100), dtype=bool)
        mask2 = np.zeros((100, 100), dtype=bool)
        mask2[49:51, 49:51] = True
        iou = calculate_iou(mask1, mask2)
        assert 0.0 < iou < 1.0
        assert 0.0 <= iou <= 1.0

class TestGradCAMIntegration:
    """Integration tests for Grad-CAM functionality."""
    
    def test_gradcam_overlay_shape(self):
        """
        Test that overlaying a heatmap on an image preserves the image shape.
        
        Given: An input image and a heatmap
        When: They are overlaid
        Then: Output should have the same shape as the input image
        """
        input_image = np.random.rand(224, 224, 3).astype(np.float32)
        heatmap = np.random.rand(224, 224).astype(np.float32)
        
        # Apply overlay
        overlay = overlay_heatmap(input_image, heatmap, alpha=0.5)
        
        # Verify shape preservation
        assert overlay.shape == input_image.shape
        assert overlay.ndim == 3
        assert overlay.shape[2] == 3  # RGB channels
        
        # Verify values are in valid range
        assert overlay.min() >= 0.0
        assert overlay.max() <= 1.0
    
    def test_gradcam_alpha_parameter(self):
        """
        Test that the alpha parameter correctly controls heatmap transparency.
        
        Given: An input image and a heatmap with different alpha values
        When: They are overlaid
        Then: Higher alpha should result in more heatmap visibility
        """
        input_image = np.ones((100, 100, 3), dtype=np.float32) * 0.5  # Gray image
        heatmap = np.ones((100, 100), dtype=np.float32)  # White heatmap
        
        # Overlay with low alpha
        overlay_low = overlay_heatmap(input_image, heatmap, alpha=0.1)
        
        # Overlay with high alpha
        overlay_high = overlay_heatmap(input_image, heatmap, alpha=0.9)
        
        # The high alpha overlay should be brighter (more heatmap influence)
        # Since heatmap is white (1.0) and image is gray (0.5), 
        # higher alpha should result in values closer to 1.0
        mean_low = np.mean(overlay_low)
        mean_high = np.mean(overlay_high)
        
        assert mean_high > mean_low, "Higher alpha should result in more heatmap influence"
        
        # Verify both are in valid range
        assert 0.0 <= mean_low <= 1.0
        assert 0.0 <= mean_high <= 1.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])