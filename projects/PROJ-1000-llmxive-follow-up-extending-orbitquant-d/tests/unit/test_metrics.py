"""
Contract tests for metric calculation functions in code/evaluation/metrics.py.

These tests verify the API contract and correctness of FID, CLIP, and MSE
calculations without requiring heavy model inference on large datasets.
"""

import pytest
import numpy as np
import torch
from pathlib import Path
import json
import tempfile
import os

# Import the target functions
from evaluation.metrics import (
    compute_mse,
    compute_clip_score,
    compute_fid,
    compute_metrics_batch,
    save_metrics_to_json,
    load_metrics_from_json,
)

# Fixtures
@pytest.fixture
def dummy_images():
    """Generate small dummy images (10x10 RGB) for testing."""
    # Shape: (batch_size, channels, height, width)
    return torch.randn(2, 3, 10, 10)

@pytest.fixture
def dummy_generated_images():
    """Generate small dummy generated images for testing."""
    return torch.randn(2, 3, 10, 10)

@pytest.fixture
def dummy_features():
    """Generate dummy CLIP features (batch_size, feature_dim)."""
    return torch.randn(2, 512)  # Typical CLIP feature dimension

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for output files."""
    output_dir = tmp_path / "metrics_output"
    output_dir.mkdir(exist_ok=True)
    return output_dir

class TestComputeMSE:
    """Tests for the MSE calculation function."""

    def test_compute_mse_basic(self, dummy_images, dummy_generated_images):
        """Test basic MSE computation between two identical tensors."""
        # MSE of identical tensors should be 0
        mse = compute_mse(dummy_images, dummy_images)
        assert mse == 0.0

    def test_compute_mse_different_tensors(self, dummy_images, dummy_generated_images):
        """Test MSE computation between different tensors."""
        mse = compute_mse(dummy_images, dummy_generated_images)
        assert mse > 0.0
        assert isinstance(mse, float)

    def test_compute_mse_dtype_handling(self):
        """Test that MSE handles float32 and float64 correctly."""
        images_f32 = torch.randn(2, 3, 10, 10, dtype=torch.float32)
        images_f64 = images_f32.clone().to(dtype=torch.float64)

        mse_f32 = compute_mse(images_f32, images_f32)
        mse_f64 = compute_mse(images_f64, images_f64)

        assert mse_f32 == 0.0
        assert mse_f64 == 0.0

    def test_compute_mse_batch_size_mismatch(self, dummy_images):
        """Test that MSE raises an error for mismatched batch sizes."""
        different_size_images = torch.randn(3, 3, 10, 10)

        with pytest.raises(RuntimeError):
            compute_mse(dummy_images, different_size_images)

    def test_compute_mse_channel_mismatch(self, dummy_images):
        """Test that MSE raises an error for mismatched channels."""
        different_channel_images = torch.randn(2, 4, 10, 10)

        with pytest.raises(RuntimeError):
            compute_mse(dummy_images, different_channel_images)

class TestComputeClipScore:
    """Tests for the CLIP score calculation function."""

    def test_compute_clip_score_basic(self, dummy_images, dummy_features):
        """Test basic CLIP score computation."""
        # Note: This test uses a simplified mock approach since real CLIP
        # requires downloading models. We test the function structure.
        # In a real scenario, this would call the CLIP model.
        # For now, we verify the function accepts correct inputs.
        score = compute_clip_score(dummy_images, dummy_features)
        assert isinstance(score, float)
        # CLIP scores are typically in a reasonable range (e.g., 0-100)
        # This is a sanity check, not a precise validation
        assert score >= 0.0

    def test_compute_clip_score_shape_validation(self, dummy_features):
        """Test that CLIP score raises error for incorrect image shapes."""
        bad_images = torch.randn(2, 1, 10, 10)  # Wrong channels

        with pytest.raises(RuntimeError):
            compute_clip_score(bad_images, dummy_features)

class TestComputeFID:
    """Tests for the FID calculation function."""

    def test_compute_fid_basic(self, dummy_images, dummy_generated_images):
        """Test basic FID computation."""
        # FID of identical distributions should be close to 0
        fid = compute_fid(dummy_images, dummy_images)
        assert fid >= 0.0
        assert isinstance(fid, float)

    def test_compute_fid_different_distributions(self, dummy_images, dummy_generated_images):
        """Test FID computation for different distributions."""
        fid = compute_fid(dummy_images, dummy_generated_images)
        assert fid >= 0.0
        # FID should be positive for different distributions
        assert fid > 0.0

    def test_compute_fid_batch_size_mismatch(self, dummy_images):
        """Test that FID handles batch size mismatch gracefully."""
        different_size_images = torch.randn(3, 3, 10, 10)

        # FID implementation may handle this differently depending on
        # the underlying statistics calculation. We test that it doesn't crash
        # with an invalid shape error
        fid = compute_fid(dummy_images, different_size_images)
        assert isinstance(fid, float)

class TestComputeMetricsBatch:
    """Tests for batch metric computation."""

    def test_compute_metrics_batch_returns_dict(self, dummy_images, dummy_generated_images, dummy_features):
        """Test that batch metrics return a dictionary with expected keys."""
        metrics = compute_metrics_batch(
            dummy_images,
            dummy_generated_images,
            dummy_features
        )

        assert isinstance(metrics, dict)
        assert "mse" in metrics
        assert "clip_score" in metrics
        assert "fid" in metrics

    def test_compute_metrics_batch_values_are_float(self, dummy_images, dummy_generated_images, dummy_features):
        """Test that all metric values are floats."""
        metrics = compute_metrics_batch(
            dummy_images,
            dummy_generated_images,
            dummy_features
        )

        for key, value in metrics.items():
            assert isinstance(value, float), f"Metric {key} should be float, got {type(value)}"

class TestSaveAndLoadMetrics:
    """Tests for saving and loading metrics to/from JSON."""

    def test_save_and_load_metrics_roundtrip(self, temp_output_dir):
        """Test that metrics can be saved and loaded correctly."""
        metrics = {
            "mse": 0.123,
            "clip_score": 45.67,
            "fid": 12.34,
            "num_samples": 100
        }

        output_path = temp_output_dir / "test_metrics.json"

        # Save
        save_metrics_to_json(metrics, str(output_path))
        assert output_path.exists()

        # Load
        loaded_metrics = load_metrics_from_json(str(output_path))

        # Verify
        assert loaded_metrics == metrics

    def test_save_metrics_creates_file(self, temp_output_dir):
        """Test that save_metrics creates the output file."""
        metrics = {"mse": 0.5, "clip_score": 50.0, "fid": 5.0}
        output_path = temp_output_dir / "new_metrics.json"

        save_metrics_to_json(metrics, str(output_path))
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_load_metrics_nonexistent_file(self):
        """Test that loading from a nonexistent file raises an error."""
        with pytest.raises(FileNotFoundError):
            load_metrics_from_json("/nonexistent/path/metrics.json")

    def test_load_metrics_invalid_json(self, temp_output_dir):
        """Test that loading invalid JSON raises an error."""
        output_path = temp_output_dir / "invalid.json"
        output_path.write_text("not valid json {{{")

        with pytest.raises(json.JSONDecodeError):
            load_metrics_from_json(str(output_path))

    def test_save_metrics_with_complex_types(self, temp_output_dir):
        """Test saving metrics with nested structures."""
        metrics = {
            "mse": 0.123,
            "details": {
                "layer_1": 0.1,
                "layer_2": 0.2
            },
            "metadata": {
                "model": "test_model",
                "version": 1.0
            }
        }

        output_path = temp_output_dir / "complex_metrics.json"
        save_metrics_to_json(metrics, str(output_path))

        loaded = load_metrics_from_json(str(output_path))
        assert loaded == metrics

class TestContractCompliance:
    """Tests to verify the API contract matches specifications."""

    def test_compute_mse_signature(self):
        """Verify compute_mse accepts two tensors and returns a float."""
        import inspect
        sig = inspect.signature(compute_mse)
        params = list(sig.parameters.keys())
        assert "real_images" in params or "images" in params
        assert "generated_images" in params or "other" in params

    def test_compute_clip_score_signature(self):
        """Verify compute_clip_score accepts images and features."""
        import inspect
        sig = inspect.signature(compute_clip_score)
        params = list(sig.parameters.keys())
        # At minimum, it should accept images and features
        assert len(params) >= 2

    def test_compute_fid_signature(self):
        """Verify compute_fid accepts real and generated images."""
        import inspect
        sig = inspect.signature(compute_fid)
        params = list(sig.parameters.keys())
        assert len(params) >= 2

    def test_save_metrics_to_json_signature(self):
        """Verify save_metrics_to_json accepts metrics dict and path."""
        import inspect
        sig = inspect.signature(save_metrics_to_json)
        params = list(sig.parameters.keys())
        assert "metrics" in params
        assert "path" in params or "filepath" in params

    def test_load_metrics_from_json_signature(self):
        """Verify load_metrics_from_json accepts a path."""
        import inspect
        sig = inspect.signature(load_metrics_from_json)
        params = list(sig.parameters.keys())
        assert "path" in params or "filepath" in params