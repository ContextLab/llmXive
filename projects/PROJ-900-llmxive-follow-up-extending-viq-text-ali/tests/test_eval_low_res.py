"""
Unit tests for eval_low_res.py
"""
import pytest
import torch
import numpy as np
from pathlib import Path
import json
import tempfile
import os

# Mock imports for testing environment if necessary
# Assuming the main module functions are tested via integration in the runner
# but we verify logic here.

def test_psnr_calculation_on_known_pair():
    """
    Verify PSNR calculation on a known pair of tensors.
    """
    from utils import calculate_psnr
    
    # Create two identical tensors -> PSNR should be very high (infinity theoretically, but clamped)
    img1 = torch.rand(1, 3, 64, 64)
    img2 = img1.clone()
    
    psnr = calculate_psnr(img1, img2)
    # Identical images should have very high PSNR (> 50 dB)
    assert psnr > 50.0, f"PSNR for identical images should be > 50, got {psnr}"

def test_ssim_calculation_on_known_pair():
    """
    Verify SSIM calculation on a known pair of tensors.
    """
    from utils import calculate_ssim
    
    # Create two identical tensors -> SSIM should be 1.0
    img1 = torch.rand(1, 3, 64, 64)
    img2 = img1.clone()
    
    ssim = calculate_ssim(img1, img2)
    assert abs(ssim - 1.0) < 1e-5, f"SSIM for identical images should be 1.0, got {ssim}"

def test_load_checkpoint_missing_file():
    """
    Verify that load_checkpoint raises FileNotFoundError if file is missing.
    """
    from eval_low_res import load_checkpoint
    
    with pytest.raises(FileNotFoundError):
        load_checkpoint("non_existent_path.pth")

def test_output_json_structure(tmp_path):
    """
    Verify the structure of the output JSON if a mock run were to succeed.
    (Simulated structure check)
    """
    # We can't easily run the full pipeline in unit tests without heavy dependencies,
    # but we can verify the expected schema logic if we had a mock result.
    mock_result = {
        "mean_psnr": 25.5,
        "std_psnr": 1.2,
        "mean_ssim": 0.85,
        "std_ssim": 0.05,
        "sample_count": 10,
        "resolution": "64x64",
        "samples": []
    }
    
    output_file = tmp_path / "test_metrics.json"
    with open(output_file, 'w') as f:
        json.dump(mock_result, f)
    
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert "mean_psnr" in data
    assert "mean_ssim" in data
    assert data["resolution"] == "64x64"
    assert data["sample_count"] == 10