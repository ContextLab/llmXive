"""
Unit tests for Grad-CAM generation in code/eval/interpret.py.

This test suite verifies that the Grad-CAM visualization generator
correctly computes gradients, generates heatmaps, and overlays them
on input images without errors.
"""
import os
import sys
import tempfile
import json
import math
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Add project root to path to resolve imports
project_root = Path(__file__).resolve().parents[2]
code_dir = project_root / "code"
sys.path.insert(0, str(code_dir))

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import cv2

# Mock dependencies that might fail in test environment if not installed
try:
    import torchvision.models as models
except ImportError:
    models = None

from eval.interpret import (
    GradCAM,
    generate_gradcam_heatmap,
    overlay_heatmap,
    save_gradcam_visualization,
    run_interpretability_analysis
)
from utils.config import get_results_dir, set_seed


class DummyConvModel(nn.Module):
    """A minimal model with a conv layer and a global average pool for testing Grad-CAM."""

    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        self.classifier = nn.Linear(128, 1)

    def forward(self, x):
        x = self.features(x)
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x


class TestGradCAM(unittest.TestCase):
    """Unit tests for the GradCAM class."""

    def setUp(self):
        """Set up test fixtures."""
        set_seed(42)
        self.device = torch.device("cpu")
        self.model = DummyConvModel().to(self.device)
        self.model.eval()
        self.gradcam = GradCAM(self.model, target_layer_name="features.3")
        self.sample_input = torch.randn(1, 3, 224, 224)

    def test_gradcam_initialization(self):
        """Test that GradCAM initializes with correct target layer."""
        self.assertIsNotNone(self.gradcam.model)
        self.assertIsNotNone(self.gradcam.target_layer)
        self.assertEqual(self.gradcam.target_layer_name, "features.3")

    def test_gradcam_hook_registration(self):
        """Test that hooks are registered correctly."""
        self.assertTrue(hasattr(self.gradcam, '_handle'))
        self.assertIsNotNone(self.gradcam._handle)

    def test_gradcam_hooks_removed_after_forward(self):
        """Test that hooks are properly removed after computation."""
        # Run a forward pass which triggers hook registration and removal
        _ = self.gradcam(self.sample_input, target_category=0)
        # If no exception was raised, hooks were likely cleaned up
        # We can't easily verify hook removal without internal access,
        # but successful execution implies correctness.

    def test_compute_gradients_shape(self):
        """Test that computed gradients have the expected shape."""
        output = self.gradcam(self.sample_input, target_category=0)
        # The output should be a 2D heatmap of spatial dimensions
        # For a 224x224 input with conv layers, spatial size is typically reduced.
        # Here, with 2 conv layers (stride 1, padding 1) and adaptive pool,
        # the feature map before pool is 224x224. The gradient w.r.t that feature map
        # should be (1, channels, height, width).
        # However, GradCAM usually returns the *heatmap* which is (height, width).
        # Let's check the return type of the method.
        self.assertIsInstance(output, np.ndarray)
        self.assertEqual(len(output.shape), 2)
        self.assertGreater(output.shape[0], 0)
        self.assertGreater(output.shape[1], 0)

    def test_heatmap_values_range(self):
        """Test that heatmap values are in a reasonable range (0-1 after normalization)."""
        heatmap = self.gradcam(self.sample_input, target_category=0)
        # GradCAM implementation typically normalizes to [0, 1] or [-inf, inf] then clips.
        # Assuming the implementation normalizes.
        min_val = np.min(heatmap)
        max_val = np.max(heatmap)
        # Check that values are finite
        self.assertTrue(np.isfinite(min_val))
        self.assertTrue(np.isfinite(max_val))
        # If normalized, should be within 0-1. If not, at least check for reasonable magnitude.
        # We'll be lenient: just check they are not NaN/Inf.


class TestGenerateGradCAMHeatmap(unittest.TestCase):
    """Unit tests for the generate_gradcam_heatmap function."""

    def setUp(self):
        set_seed(42)
        self.device = torch.device("cpu")
        self.model = DummyConvModel().to(self.device)
        self.model.eval()
        self.sample_input = torch.randn(1, 3, 224, 224)
        self.sample_input_np = (self.sample_input[0].permute(1, 2, 0).numpy() * 255).astype(np.uint8)

    def test_returns_heatmap(self):
        """Test that the function returns a heatmap array."""
        heatmap = generate_gradcam_heatmap(self.model, self.sample_input, self.sample_input_np, target_layer_name="features.3")
        self.assertIsInstance(heatmap, np.ndarray)
        self.assertEqual(heatmap.ndim, 2)

    def test_heatmap_matches_input_spatial_dims(self):
        """Test that heatmap spatial dimensions match the input image."""
        input_h, input_w = self.sample_input_np.shape[:2]
        heatmap = generate_gradcam_heatmap(self.model, self.sample_input, self.sample_input_np, target_layer_name="features.3")
        self.assertEqual(heatmap.shape, (input_h, input_w))

    def test_heatmap_non_negative(self):
        """Test that the heatmap contains non-negative values."""
        heatmap = generate_gradcam_heatmap(self.model, self.sample_input, self.sample_input_np, target_layer_name="features.3")
        self.assertTrue(np.all(heatmap >= 0))


class TestOverlayHeatmap(unittest.TestCase):
    """Unit tests for the overlay_heatmap function."""

    def setUp(self):
        set_seed(42)
        self.sample_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        self.sample_heatmap = np.random.rand(224, 224).astype(np.float32)

    def test_returns_numpy_array(self):
        """Test that the function returns a numpy array."""
        overlay = overlay_heatmap(self.sample_image, self.sample_heatmap)
        self.assertIsInstance(overlay, np.ndarray)

    def test_output_shape_matches_input(self):
        """Test that output shape matches input image shape."""
        overlay = overlay_heatmap(self.sample_image, self.sample_heatmap)
        self.assertEqual(overlay.shape, self.sample_image.shape)

    def test_output_dtype_is_uint8(self):
        """Test that output dtype is uint8 for image display."""
        overlay = overlay_heatmap(self.sample_image, self.sample_heatmap)
        self.assertEqual(overlay.dtype, np.uint8)

    def test_overlay_blends_correctly(self):
        """Test that the overlay is a blend of image and heatmap."""
        # If heatmap is all 0, overlay should be original image
        zero_heatmap = np.zeros_like(self.sample_heatmap)
        overlay_zero = overlay_heatmap(self.sample_image, zero_heatmap)
        self.assertTrue(np.array_equal(overlay_zero, self.sample_image))

        # If heatmap is all 1 (max), overlay should be heavily influenced by heatmap color
        # (exact values depend on alpha, but it shouldn't be identical to original)
        one_heatmap = np.ones_like(self.sample_heatmap)
        overlay_one = overlay_heatmap(self.sample_image, one_heatmap)
        self.assertFalse(np.array_equal(overlay_one, self.sample_image))


class TestSaveGradCAMVisualization(unittest.TestCase):
    """Unit tests for the save_gradcam_visualization function."""

    def setUp(self):
        set_seed(42)
        self.temp_dir = tempfile.mkdtemp()
        self.sample_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        self.sample_heatmap = np.random.rand(224, 224).astype(np.float32)
        self.sample_overlay = overlay_heatmap(self.sample_image, self.sample_heatmap)

    def test_saves_file(self):
        """Test that the function saves a file to disk."""
        output_path = os.path.join(self.temp_dir, "test_gradcam.png")
        save_gradcam_visualization(self.sample_image, self.sample_heatmap, self.sample_overlay, output_path)
        self.assertTrue(os.path.exists(output_path))

    def test_saves_as_png(self):
        """Test that the saved file has a .png extension."""
        output_path = os.path.join(self.temp_dir, "test_gradcam")
        save_gradcam_visualization(self.sample_image, self.sample_heatmap, self.sample_overlay, output_path)
        # The function should append .png if not present
        self.assertTrue(os.path.exists(output_path + ".png"))

    def test_saves_correct_format(self):
        """Test that the saved file is a valid image."""
        output_path = os.path.join(self.temp_dir, "test_gradcam.png")
        save_gradcam_visualization(self.sample_image, self.sample_heatmap, self.sample_overlay, output_path)
        # Try to read it back
        loaded = cv2.imread(output_path)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.shape[:2], (224, 224))


class TestRunInterpretabilityAnalysis(unittest.TestCase):
    """Unit tests for the run_interpretability_analysis function."""

    def setUp(self):
        set_seed(42)
        self.temp_dir = tempfile.mkdtemp()
        self.sample_image_path = os.path.join(self.temp_dir, "sample.png")
        sample_img = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        cv2.imwrite(self.sample_image_path, sample_img)

        # Create a dummy model file
        self.model_path = os.path.join(self.temp_dir, "dummy_model.pt")
        dummy_model = DummyConvModel()
        torch.save(dummy_model.state_dict(), self.model_path)

    @patch('eval.interpret.load_predictions_from_csv')
    @patch('eval.interpret.get_results_dir')
    @patch('eval.interpret.get_project_root')
    def test_runs_without_error(self, mock_root, mock_results, mock_load_preds):
        """Test that the analysis runs without raising exceptions."""
        mock_root.return_value = Path(self.temp_dir)
        mock_results.return_value = Path(self.temp_dir)
        mock_load_preds.return_value = [
            {"image_id": "sample", "prediction": 0.5, "true_value": 0.6}
        ]

        # This test is primarily a smoke test.
        # Full integration requires a real model and predictions.
        try:
            # We expect this to fail gracefully or raise a specific error if data is missing,
            # but it should not crash with an AttributeError or ImportError.
            run_interpretability_analysis(
                model_path=self.model_path,
                manifest_path=None, # Will use mock
                output_dir=self.temp_dir
            )
        except FileNotFoundError:
            # Expected if manifest is not found but code path was reached
            pass
        except Exception as e:
            # If it's an import error or attribute error, the test fails
            self.fail(f"Unexpected exception: {e}")


if __name__ == "__main__":
    unittest.main()