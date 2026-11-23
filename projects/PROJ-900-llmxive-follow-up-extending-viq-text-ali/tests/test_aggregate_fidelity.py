"""
Tests for the metric aggregation script (T021).
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Mock the config to avoid dependency on full setup for unit tests
# We patch the get_config function to return a minimal valid config object
class MockConfig:
    def __init__(self):
        self.paths = MagicMock()
        self.paths.results_dir = tempfile.gettempdir()

def test_metric_aggregation_logic():
    """
    Test that the metric calculation logic works correctly on synthetic but real-data-like inputs.
    Note: This test uses deterministic synthetic arrays to verify the math, 
    not to simulate the 'real data fetch' requirement of the main script.
    """
    from code.utils import calculate_psnr, calculate_ssim

    # Create a known perfect match (PSNR should be high/infinite, SSIM 1.0)
    # Using uint8 0-255 range
    img1 = np.ones((3, 64, 64), dtype=np.uint8) * 128
    img2 = img1.copy()

    # Calculate expected values manually or via utils
    psnr_val = calculate_psnr(img1, img2)
    ssim_val = calculate_ssim(img1, img2)

    # PSNR for identical images is technically infinite, but utils might cap it or return a large number
    # SSIM for identical images should be 1.0
    assert psnr_val >= 40.0, "PSNR for identical images should be very high"
    assert abs(ssim_val - 1.0) < 1e-5, "SSIM for identical images should be 1.0"

    # Create a noisy image (PSNR should be lower)
    img3 = img1.astype(np.float32) + np.random.normal(0, 10, img1.shape).astype(np.float32)
    img3 = np.clip(img3, 0, 255).astype(np.uint8)

    psnr_noisy = calculate_psnr(img1, img3)
    ssim_noisy = calculate_ssim(img1, img3)

    assert psnr_noisy < psnr_val, "Noisy image should have lower PSNR"
    assert ssim_noisy < ssim_val, "Noisy image should have lower SSIM"

def test_aggregate_script_output_structure():
    """
    Test that the script produces the correct JSON structure when run.
    """
    import sys
    from io import StringIO
    
    # Create temporary files for input
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        recon_path = tmpdir_path / "reconstructions_high_res.npz"
        orig_path = tmpdir_path / "original_images_high_res.npz"
        output_path = tmpdir_path / "fidelity_metrics.json"

        # Generate dummy data
        # Shape: (N, C, H, W) -> (10, 3, 64, 64)
        N, C, H, W = 10, 3, 64, 64
        originals = np.random.randint(0, 256, (N, C, H, W), dtype=np.uint8)
        reconstructions = originals.copy() # Perfect match for simplicity

        np.savez(recon_path, reconstructions=reconstructions)
        np.savez(orig_path, originals=originals)

        # Mock get_config to point to this temp dir
        with patch('code.aggregate_fidelity_metrics.get_config') as mock_get_config:
            mock_cfg = MockConfig()
            mock_cfg.paths.results_dir = str(tmpdir_path)
            mock_get_config.return_value = mock_cfg

            # Import after patching to ensure it picks up the mock
            # We need to reload the module or import it fresh if it was already imported
            # For this test, we assume it's not imported yet or we use a fresh namespace
            # Simulating the script execution
            from code.aggregate_fidelity_metrics import main
            
            # Run main with specific args to ensure we hit the temp files
            import argparse
            args = argparse.Namespace(
                recon_path=str(recon_path),
                orig_path=str(orig_path),
                output_path=str(output_path)
            )
            
            # Capture stdout to verify logging
            captured_output = StringIO()
            sys.stdout = captured_output
            
            try:
                result = main(args)
            finally:
                sys.stdout = sys.__stdout__

            # Verify output file exists
            assert output_path.exists(), f"Output file {output_path} was not created"

            # Verify JSON content
            with open(output_path, 'r') as f:
                data = json.load(f)

            assert "mean_psnr" in data, "Missing mean_psnr in output"
            assert "mean_ssim" in data, "Missing mean_ssim in output"
            assert "count" in data, "Missing count in output"
            assert "note" in data, "Missing note in output"
            
            assert data["count"] == N, f"Count mismatch: expected {N}, got {data['count']}"
            assert "native ground truth used per Plan Amendment" in data["note"], "Note text incorrect"
            
            # Verify types
            assert isinstance(data["mean_psnr"], float)
            assert isinstance(data["mean_ssim"], float)
            assert isinstance(data["count"], int)

def test_missing_input_files_raises_error():
    """
    Verify that the script fails loudly if input files are missing.
    """
    import argparse
    from code.aggregate_fidelity_metrics import main

    with tempfile.TemporaryDirectory() as tmpdir:
        args = argparse.Namespace(
            recon_path=str(Path(tmpdir) / "nonexistent.npz"),
            orig_path=str(Path(tmpdir) / "nonexistent.npz"),
            output_path=str(Path(tmpdir) / "out.json")
        )

        with pytest.raises(FileNotFoundError):
            main(args)