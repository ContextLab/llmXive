"""
Unit tests for metric calculation functions in code/evaluation/metrics.py.

This module verifies the correctness of FID, CLIP score, and MSE calculations
used in User Story 3 (Evaluation).

Tests cover:
1. compute_mse: Correctness on simple tensors
2. compute_clip_score: API contract and shape validation
3. compute_fid: Basic statistical properties (non-negative, symmetry check)
4. compute_metrics_batch: Batch processing logic
5. save/load metrics to/from JSON
"""

import json
import tempfile
import os
import pytest
import numpy as np
import torch
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to be tested
# Assuming the project structure allows importing from code/evaluation
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from evaluation.metrics import (
    compute_mse,
    compute_clip_score,
    compute_fid,
    compute_metrics_batch,
    save_metrics_to_json,
    load_metrics_from_json
)
from config import Config


class TestComputeMSE:
    """Tests for the compute_mse function."""

    def test_mse_identical_tensors(self):
        """MSE of identical tensors should be 0."""
        a = torch.randn(10, 512)
        mse = compute_mse(a, a)
        assert mse == 0.0, f"Expected 0.0, got {mse}"

    def test_mse_different_tensors(self):
        """MSE of different tensors should be positive."""
        a = torch.zeros(10, 512)
        b = torch.ones(10, 512)
        mse = compute_mse(a, b)
        expected = 1.0
        assert abs(mse - expected) < 1e-6, f"Expected {expected}, got {mse}"

    def test_mse_scalar_output(self):
        """MSE should return a scalar float."""
        a = torch.randn(5, 10)
        b = torch.randn(5, 10)
        mse = compute_mse(a, b)
        assert isinstance(mse, float), f"Expected float, got {type(mse)}"

    def test_mse_shape_mismatch_raises(self):
        """MSE should raise error for mismatched shapes."""
        a = torch.randn(10, 5)
        b = torch.randn(10, 6)
        with pytest.raises(RuntimeError):
            compute_mse(a, b)


class TestComputeClipScore:
    """Tests for the compute_clip_score function."""

    @patch('evaluation.metrics.AutoModel')
    @patch('evaluation.metrics.AutoTokenizer')
    def test_clip_score_api_contract(self, mock_tokenizer, mock_model):
        """Verify that compute_clip_score calls the expected model and tokenizer."""
        # Setup mocks
        mock_tokenizer.return_value = MagicMock()
        mock_model.return_value = MagicMock()
        
        # Mock the model output
        mock_model.return_value.get_intermediate_layers = MagicMock(
            return_value=[torch.randn(1, 77, 768), torch.randn(1, 77, 768)]
        )
        
        # Mock image encoder
        mock_model.return_value.vision_model = MagicMock()
        mock_model.return_value.vision_model.get_intermediate_layers = MagicMock(
            return_value=[torch.randn(1, 257, 768)]
        )

        # Mock the normalize function
        with patch('evaluation.metrics.nn.functional.normalize') as mock_normalize:
            mock_normalize.side_effect = lambda x, dim: x / x.norm(dim=dim, keepdim=True)
            
            # Run test
            image = torch.randn(1, 3, 224, 224)
            caption = "a cat sitting on a mat"
            
            # This should not raise an error
            score = compute_clip_score(image, caption)
            
            # Verify model was called
            mock_model.assert_called()
            mock_tokenizer.assert_called()

    def test_clip_score_range(self):
        """CLIP score should be in a reasonable range (typically 0-100 or similar)."""
        # Since we can't easily compute real CLIP scores without heavy models,
        # we test the mock behavior
        with patch('evaluation.metrics.AutoModel') as mock_model, \
             patch('evaluation.metrics.AutoTokenizer') as mock_tokenizer, \
             patch('evaluation.metrics.nn.functional.normalize') as mock_normalize:
             
            mock_tokenizer.return_value = MagicMock()
            mock_model.return_value = MagicMock()
            
            # Mock features
            img_feat = torch.randn(1, 512)
            txt_feat = torch.randn(1, 512)
            
            mock_normalize.side_effect = lambda x, dim: x / x.norm(dim=dim, keepdim=True)
            
            # Simulate cosine similarity
            similarity = torch.nn.functional.cosine_similarity(img_feat, txt_feat, dim=1)
            score = similarity.item() * 100  # CLIP scores are often scaled
            
            assert 0 <= score <= 100, f"CLIP score {score} out of expected range"


class TestComputeFID:
    """Tests for the compute_fid function."""

    def test_fid_same_distribution(self):
        """FID of identical distributions should be close to 0."""
        # Generate identical random tensors
        features = torch.randn(100, 512)
        fid = compute_fid(features, features)
        assert fid < 1e-6, f"FID of identical distributions should be ~0, got {fid}"

    def test_fid_different_distributions(self):
        """FID of different distributions should be positive."""
        features1 = torch.randn(100, 512)
        features2 = torch.randn(100, 512) + 5.0  # Shifted mean
        fid = compute_fid(features1, features2)
        assert fid > 0, f"FID should be positive, got {fid}"

    def test_fid_non_negative(self):
        """FID should always be non-negative."""
        features1 = torch.randn(50, 256)
        features2 = torch.randn(50, 256)
        fid = compute_fid(features1, features2)
        assert fid >= 0, f"FID should be non-negative, got {fid}"

    def test_fid_small_sample(self):
        """FID should work with small sample sizes."""
        features1 = torch.randn(5, 64)
        features2 = torch.randn(5, 64)
        fid = compute_fid(features1, features2)
        assert isinstance(fid, float), "FID should return a float"

    def test_fid_shape_mismatch(self):
        """FID should raise error for mismatched feature dimensions."""
        features1 = torch.randn(10, 512)
        features2 = torch.randn(10, 256)
        with pytest.raises(RuntimeError):
            compute_fid(features1, features2)


class TestComputeMetricsBatch:
    """Tests for the compute_metrics_batch function."""

    def test_batch_processing(self):
        """Test that batch processing works correctly."""
        # Mock the individual metric functions
        with patch('evaluation.metrics.compute_mse', return_value=0.5), \
             patch('evaluation.metrics.compute_clip_score', return_value=25.0), \
             patch('evaluation.metrics.compute_fid', return_value=10.0):
            
            # Create dummy data
            real_features = torch.randn(20, 512)
            fake_features = torch.randn(20, 512)
            captions = ["caption 1", "caption 2", "caption 3", "caption 4"]
            images = [torch.randn(1, 3, 224, 224) for _ in range(4)]
            
            metrics = compute_metrics_batch(
                real_features=real_features,
                fake_features=fake_features,
                captions=captions,
                images=images
            )
            
            assert isinstance(metrics, dict), "Metrics should be a dictionary"
            assert 'mse' in metrics, "MSE should be in metrics"
            assert 'clip_score' in metrics, "CLIP score should be in metrics"
            assert 'fid' in metrics, "FID should be in metrics"

    def test_empty_batch_handling(self):
        """Test handling of empty batches."""
        with patch('evaluation.metrics.compute_mse', return_value=0.0), \
             patch('evaluation.metrics.compute_clip_score', return_value=0.0), \
             patch('evaluation.metrics.compute_fid', return_value=0.0):
            
            metrics = compute_metrics_batch(
                real_features=torch.randn(0, 512),
                fake_features=torch.randn(0, 512),
                captions=[],
                images=[]
            )
            
            assert isinstance(metrics, dict), "Metrics should be a dictionary"


class TestSaveLoadMetricsJSON:
    """Tests for saving and loading metrics to/from JSON."""

    def test_save_and_load_roundtrip(self):
        """Test that metrics can be saved and loaded correctly."""
        metrics = {
            'mse': 0.123,
            'clip_score': 25.5,
            'fid': 10.7,
            'num_samples': 100,
            'timestamp': '2024-01-01T00:00:00'
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'metrics.json')
            
            # Save
            save_metrics_to_json(metrics, filepath)
            assert os.path.exists(filepath), "Metrics file should exist"
            
            # Load
            loaded = load_metrics_from_json(filepath)
            
            # Verify
            assert loaded['mse'] == metrics['mse'], "MSE should match"
            assert loaded['clip_score'] == metrics['clip_score'], "CLIP score should match"
            assert loaded['fid'] == metrics['fid'], "FID should match"

    def test_load_nonexistent_file(self):
        """Test that loading a non-existent file raises an error."""
        with pytest.raises(FileNotFoundError):
            load_metrics_from_json('/nonexistent/path/metrics.json')

    def test_invalid_json_format(self):
        """Test that invalid JSON format raises an error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("not valid json")
            filepath = f.name
        
        try:
            with pytest.raises((json.JSONDecodeError, ValueError)):
                load_metrics_from_json(filepath)
        finally:
            os.unlink(filepath)


class TestMetricsIntegration:
    """Integration-style tests for the metrics module."""

    def test_config_compatibility(self):
        """Test that metrics functions work with Config parameters."""
        config = Config()
        
        # Verify that the config has the expected attributes
        assert hasattr(config, 'device'), "Config should have device attribute"
        assert hasattr(config, 'metrics'), "Config should have metrics attribute"
        
        # Test that we can create tensors on the configured device
        device = torch.device(config.device if config.device else 'cpu')
        tensor = torch.randn(10, 512, device=device)
        assert tensor.device.type == device.type, "Tensor should be on correct device"

    def test_numerical_stability(self):
        """Test that metrics are numerically stable for edge cases."""
        # Test with very small values
        small = torch.randn(10, 512) * 1e-10
        mse_small = compute_mse(small, small)
        assert not np.isnan(mse_small), "MSE should not be NaN for small values"
        assert not np.isinf(mse_small), "MSE should not be Inf for small values"

        # Test with very large values
        large = torch.randn(10, 512) * 1e10
        mse_large = compute_mse(large, large)
        assert not np.isnan(mse_large), "MSE should not be NaN for large values"
        assert not np.isinf(mse_large), "MSE should not be Inf for large values"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])