"""
Unit tests for the calibration module.
"""
import os
import json
import tempfile
import pytest
import numpy as np
from pathlib import Path
import rasterio
from rasterio.transform import from_bounds

# Import the function to test
# Assuming calibration.py is in the code directory and we can import it
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from calibration import estimate_lambda, _create_lag_matrix_binary, _log_likelihood_sar


def test_create_lag_matrix_binary():
    """Test the binary weights matrix creation."""
    # Create 4 points in a square
    coords = np.array([
        [0.0, 0.0],
        [1.0, 0.0],
        [0.0, 1.0],
        [1.0, 1.0]
    ])

    # Threshold = 1.5 (should connect diagonals too)
    W = _create_lag_matrix_binary(coords, threshold=1.5)

    # Diagonal should be zero
    assert np.allclose(np.diag(W), 0.0)
    # Row sums should be 1.0 (row‑standardised)
    assert np.allclose(W.sum(axis=1), 1.0)

    # Smaller threshold (only orthogonal neighbours)
    W_small = _create_lag_matrix_binary(coords, threshold=1.1)
    # (0,0) should NOT be connected to (1,1)
    assert W_small[0, 3] == 0.0
    # (0,0) should be connected to (1,0)
    assert W_small[0, 1] > 0.0


def test_log_likelihood_sar():
    """Test the Gaussian SAR log‑likelihood implementation."""
    y = np.array([1.0, 0.0, 1.0, 0.0])
    W = np.eye(4)  # Identity (no spatial dependence)

    ll = _log_likelihood_sar(y, W, rho=0.0, sigma2=1.0)

    # With rho=0 and sigma2=1, the LL reduces to the standard normal LL
    expected = -0.5 * 4 * np.log(2 * np.pi) - 0.5 * np.sum(y ** 2)
    assert np.isclose(ll, expected)


def test_estimate_lambda_integration(tmp_path):
    """Integration test for ``estimate_lambda`` with a synthetic raster."""
    height, width = 100, 100
    transform = from_bounds(0, 0, 100, 100, width, height)

    # Simple block pattern: top half forest (41), bottom half other (11)
    data = np.zeros((height, width), dtype=np.uint8)
    data[:50, :] = 41
    data[50:, :] = 11

    # Write raster to temporary file
    temp_tif = tmp_path / "test_raster.tif"
    with rasterio.open(
        temp_tif,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=rasterio.uint8,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(data, 1)

    output_json = tmp_path / "calibration_test.json"

    # Run estimation
    lambda_est = estimate_lambda(
        input_path=str(temp_tif),
        output_path=str(output_json),
        sample_size=500,
        seed=42,
    )

    # Verify output file exists
    assert output_json.exists()

    # Verify JSON content
    with open(output_json, "r") as f:
        saved = json.load(f)

    assert "lambda" in saved
    assert "seed" in saved
    assert saved["seed"] == 42
    assert isinstance(saved["lambda"], float)

    # Lambda should be positive for the block pattern
    assert saved["lambda"] > 0.0