import os
import sys
import json
import numpy as np
import pytest
from pathlib import Path
import nibabel as nib

# Add code to path if not already
code_path = Path(__file__).parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from utils.logging_config import get_logger
from config import get_config

LOG = get_logger(__name__)

# Mock data generation for testing (not for production)
# This test verifies the logic of the script, assuming the script is run 
# in an environment where the data exists.
# However, per constraints, we must verify the existence of the artifact 
# and its validity if the script were to run.

# Since we cannot run the full pipeline in this test without the raw data,
# we will test the helper functions if imported, or verify the output file 
# structure if it exists.

def test_t014_artifact_exists():
    """
    Verify that T014 produces the expected artifact.
    This test is expected to FAIL if T014 has not been run successfully.
    """
    output_file = Path("data/processed/roi_left_hipp.npy")
    assert output_file.exists(), f"Artifact {output_file} not found. Run T014 first."
    
    # Load and verify shape
    data = np.load(str(output_file))
    assert isinstance(data, np.ndarray), "Output must be a numpy array"
    assert data.ndim == 2, f"Expected 2D array (subjects, timepoints), got {data.ndim}D"
    assert data.shape[0] > 0, "No subjects extracted"
    assert data.shape[1] > 0, "No timepoints extracted"
    
    # Verify dtype
    assert data.dtype in [np.float32, np.float64], f"Expected float, got {data.dtype}"

def test_t014_mask_consistency():
    """
    Verify that the mask used is consistent with the recorded paths.
    """
    mask_file = Path("data/processed/mask_paths.json")
    assert mask_file.exists(), "Mask paths file missing"
    
    with open(mask_file, 'r') as f:
        paths = json.load(f)
    
    assert 'left_hipp' in paths, "left_hipp key missing in mask_paths.json"
    assert Path(paths['left_hipp']).exists(), f"Mask file {paths['left_hipp']} not found"

def test_t014_no_nan_ratio():
    """
    Check that the data is not all NaN (indicating a failure to load voxels).
    """
    output_file = Path("data/processed/roi_left_hipp.npy")
    if not output_file.exists():
        pytest.skip("Artifact not found, skipping content check")
    
    data = np.load(str(output_file))
    nan_ratio = np.isnan(data).sum() / data.size
    # Allow some NaN if subjects had different run lengths, but not 100%
    assert nan_ratio < 0.99, f"Data is mostly NaN ({nan_ratio:.2%}). Extraction likely failed."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])