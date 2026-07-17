"""
Unit tests for code/eval_low_res.py logic.
"""
import os
import json
import tempfile
from unittest.mock import MagicMock, patch
import torch
import numpy as np
import pytest

from utils import calculate_psnr

# We test the logic of evaluation without needing the full model training
def test_psnr_calculation_on_known_pair():
    """Verify PSNR calculation on a simple known pair."""
    # Create two identical images -> PSNR should be infinity (or very high)
    img1 = np.ones((3, 64, 64), dtype=np.float32)
    img2 = np.ones((3, 64, 64), dtype=np.float32)
    
    # Add a tiny noise to avoid division by zero in log
    img2[0, 0, 0] = 0.999999
    
    psnr = calculate_psnr(img1, img2)
    assert psnr > 100.0, f"Identical images should have very high PSNR, got {psnr}"

def test_psnr_calculation_on_noisy_pair():
    """Verify PSNR calculation degrades with noise."""
    img1 = np.random.rand(3, 64, 64).astype(np.float32)
    img2 = img1 + np.random.normal(0, 0.1, img1.shape).astype(np.float32)
    img2 = np.clip(img2, 0, 1)
    
    psnr = calculate_psnr(img1, img2)
    # Noise of 0.1 should result in a finite, reasonable PSNR (not infinity)
    assert psnr < 100.0 and psnr > 0.0, f"Expected finite PSNR for noisy images, got {psnr}"

@patch('eval_low_res.get_config')
@patch('eval_low_res.get_model')
@patch('eval_low_res.COCOStreamingDataset')
@patch('eval_low_res.get_dataloader')
def test_evaluation_flow(mock_dataloader, mock_dataset, mock_get_model, mock_get_config):
    """Test the main evaluation flow with mocked dependencies."""
    # Import inside test to allow patching
    import eval_low_res
    
    # Setup mocks
    mock_config = MagicMock()
    mock_config.paths.results = tempfile.gettempdir()
    mock_config.dataset_limits = {"resolution": 64, "max_eval_samples": 2}
    mock_config.batch_size = 1
    mock_config.thresholds.semantic_threshold = 15.0
    mock_get_config.return_value = mock_config
    
    mock_model = MagicMock()
    mock_model.eval = MagicMock()
    mock_model.encode.return_value = torch.randn(1, 16, 8, 8) # Mock latent
    mock_model.quantize.return_value = (torch.randn(1, 16, 8, 8), None, None) # Mock quantized
    mock_model.decode.return_value = torch.rand(1, 3, 64, 64) # Mock reconstruction
    mock_model.to.return_value = mock_model
    mock_get_model.return_value = mock_model
    
    # Mock dataset and loader
    mock_ds_instance = MagicMock()
    mock_dataset.return_value = mock_ds_instance
    
    # Create a mock batch: 1 image of shape (3, 64, 64)
    mock_batch = {"image": torch.rand(1, 3, 64, 64)}
    mock_dataloader.return_value = iter([mock_batch, mock_batch])
    
    # Run the evaluation function directly (bypassing main() file I/O)
    results = eval_low_res.evaluate_reconstruction(
        model=mock_model,
        dataloader=mock_dataloader.return_value,
        num_samples=2,
        device="cpu"
    )
    
    # Assertions
    assert "mean_psnr" in results
    assert "count" in results
    assert results["count"] == 2
    assert mock_model.eval.called
    assert mock_model.encode.called
    assert mock_model.quantize.called
    assert mock_model.decode.called

if __name__ == "__main__":
    pytest.main([__file__, "-v"])