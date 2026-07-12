"""
Contract test for modality tensor shapes (US2).

This test verifies that the generated sensor modalities (RGB, Depth, Occupancy Grid)
adhere to the strict shape requirements defined in the project specification.
It acts as a gatekeeper for the data pipeline (T020-T022) before downstream
training tasks (T029+) can proceed.

Expected Shapes (based on spec):
- RGB: (Batch, Channels=3, Height=84, Width=84) - Center cropped and normalized
- Depth: (Batch, 1, Height=42, Width=42) - Downsampled
- Occupancy Grid: (Batch, 1, Height=42, Width=42) - Binary matrix
"""

import os
import sys
import json
import pytest
import numpy as np
from pathlib import Path

# Add src to path if not already done by conftest
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.utils.config import get_path


# Constants defined in spec
EXPECTED_RGB_SHAPE = (3, 84, 84)  # C, H, W
EXPECTED_DEPTH_SHAPE = (1, 42, 42)  # C, H, W
EXPECTED_GRID_SHAPE = (1, 42, 42)  # C, H, W
MIN_IU_THRESHOLD = 0.95


def load_generated_modalities():
    """
    Loads the generated modalities from the data directory.
    Expects the pipeline (T023) to have generated files in:
    data/modalities/{seed_id}/modalities.npz or similar structure.
    """
    modalities_dir = get_path("data_modalities")
    if not modalities_dir.exists():
        raise FileNotFoundError(
            f"Modality data directory not found at {modalities_dir}. "
            "Ensure T023 (generate_modalities.py) has been executed."
        )

    # Try to find the most recent run or a specific seed if available
    # For contract testing, we assume a consolidated file or iterate over seeds
    # Let's look for a generic 'latest' or iterate
    npz_files = list(modalities_dir.glob("**/*.npz"))
    
    if not npz_files:
        # Fallback: check for JSON reports if npz not yet generated but report exists
        # However, the contract is on TENSORS, so we need the array data.
        # If the pipeline hasn't run, this test MUST fail.
        raise FileNotFoundError(
            f"No modality .npz files found in {modalities_dir}. "
            "The data pipeline (T023) must be run first to generate tensor data."
        )

    # Load the first available modality file for shape checking
    # In a real scenario, we might aggregate, but for shape contract, one valid sample is enough.
    # We assume the file structure: { 'rgb': ..., 'depth': ..., 'grid': ... }
    sample_path = npz_files[0]
    data = np.load(sample_path)
    return data


def test_modality_files_exist():
    """Contract: Verify that modality output files exist."""
    try:
        load_generated_modalities()
    except FileNotFoundError as e:
        pytest.fail(f"Modality data files missing: {e}")


def test_modality_rgb_shape():
    """Contract: Verify RGB tensor shape is (3, 84, 84)."""
    data = load_generated_modalities()
    
    assert 'rgb' in data.files, "Missing 'rgb' key in modality file"
    rgb = data['rgb']
    
    # Handle potential batch dimension if stored as (N, C, H, W)
    # We check the last 3 dimensions or the whole shape if N=1
    if rgb.ndim == 4:
        # Assume batch dimension exists, check a single sample
        sample = rgb[0]
        shape = sample.shape
    elif rgb.ndim == 3:
        shape = rgb.shape
    else:
        pytest.fail(f"RGB tensor has unexpected dimensions: {rgb.ndim}")

    assert shape == EXPECTED_RGB_SHAPE, (
        f"RGB shape mismatch. Expected {EXPECTED_RGB_SHAPE}, got {shape}. "
        "Ensure T020 (RGB preprocessing) centers crops and resizes correctly."
    )


def test_modality_depth_shape():
    """Contract: Verify Depth tensor shape is (1, 42, 42)."""
    data = load_generated_modalities()
    
    assert 'depth' in data.files, "Missing 'depth' key in modality file"
    depth = data['depth']
    
    if depth.ndim == 4:
        sample = depth[0]
        shape = sample.shape
    elif depth.ndim == 3:
        shape = depth.shape
    else:
        pytest.fail(f"Depth tensor has unexpected dimensions: {depth.ndim}")

    assert shape == EXPECTED_DEPTH_SHAPE, (
        f"Depth shape mismatch. Expected {EXPECTED_DEPTH_SHAPE}, got {shape}. "
        "Ensure T021 (Depth downsampling) reduces resolution to 42x42."
    )


def test_modality_grid_shape():
    """Contract: Verify Occupancy Grid tensor shape is (1, 42, 42)."""
    data = load_generated_modalities()
    
    assert 'grid' in data.files, "Missing 'grid' key in modality file"
    grid = data['grid']
    
    if grid.ndim == 4:
        sample = grid[0]
        shape = sample.shape
    elif grid.ndim == 3:
        shape = grid.shape
    else:
        pytest.fail(f"Grid tensor has unexpected dimensions: {grid.ndim}")

    assert shape == EXPECTED_GRID_SHAPE, (
        f"Grid shape mismatch. Expected {EXPECTED_GRID_SHAPE}, got {shape}. "
        "Ensure T022 (Occupancy Grid generation) produces correct resolution."
    )


def test_modality_grid_binary():
    """Contract: Verify Occupancy Grid contains only binary values (0.0 or 1.0)."""
    data = load_generated_modalities()
    grid = data['grid']
    
    # Flatten and check unique values
    unique_vals = np.unique(grid)
    # Allow for small floating point errors if generated via float ops, but should be effectively 0/1
    valid_values = np.all((np.isclose(unique_vals, 0)) | np.isclose(unique_vals, 1))
    
    assert valid_values, (
        f"Occupancy Grid contains non-binary values: {unique_vals}. "
        "Ensure T022 produces a strictly binary matrix."
    )


def test_modality_alignment_report_exists():
    """Contract: Verify that the alignment report (T025) exists."""
    alignment_path = get_path("alignment_report")
    # The path helper might return a directory or specific file. 
    # T025 specifies: results/alignment_report.json
    results_dir = get_path("results")
    report_file = results_dir / "alignment_report.json"
    
    if not report_file.exists():
        pytest.fail(
            f"Alignment report missing at {report_file}. "
            "Ensure T025 (spatial alignment verification) has been executed."
        )
    
    # Verify schema of the report
    with open(report_file, 'r') as f:
        report = json.load(f)
    
    assert 'iou_scores' in report, "Missing 'iou_scores' in alignment report"
    assert isinstance(report['iou_scores'], (list, float)), "iou_scores must be numeric"
    
    # Check threshold constraint if available
    if 'min_iou' in report:
        assert report['min_iou'] >= MIN_IU_THRESHOLD, (
            f"Minimum IoU {report['min_iou']} is below threshold {MIN_IU_THRESHOLD}. "
            "Spatial alignment failed."
        )