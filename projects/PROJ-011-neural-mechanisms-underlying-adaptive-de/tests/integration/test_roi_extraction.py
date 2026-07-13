"""
Integration Test for ROI Extraction

Verifies that ROI extraction produces time series with dimensions matching the
input functional image timepoints.
"""
import os
import sys
from pathlib import Path
import tempfile
import numpy as np
import nibabel as nib
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from preprocessing.roi_extraction import extract_roi_timeseries, load_roi_masks
from utils.io import ensure_dir

@pytest.fixture
def mock_functional_image(tmp_path):
    """Create a mock 4D functional NIfTI image for testing."""
    # Dimensions: x, y, z, time
    shape = (10, 10, 10, 20)
    data = np.random.rand(*shape).astype(np.float32)
    
    # Create a simple affine
    affine = np.eye(4)
    
    img = nib.Nifti1Image(data, affine)
    
    output_path = tmp_path / "sub-test_space-MNI_desc-preproc_bold.nii.gz"
    nib.save(img, output_path)
    
    return output_path

@pytest.fixture
def mock_roi_masks(tmp_path):
    """Create mock ROI masks for testing."""
    # Create a mask that covers the center of the volume
    mask_data = np.zeros((10, 10, 10), dtype=np.int16)
    mask_data[4:6, 4:6, 4:6] = 1 # Small central cube
    
    affine = np.eye(4)
    mask_img = nib.Nifti1Image(mask_data, affine)
    
    return {
        "test_roi": mask_img
    }

def test_roi_extraction_dimensions(mock_functional_image, mock_roi_masks, tmp_path):
    """
    Test that extracted ROI time series has the correct number of timepoints.
    
    This verifies the core requirement: dimensions match timepoints.
    """
    output_dir = tmp_path / "roi_output"
    ensure_dir(output_dir)
    
    # Run extraction
    results = extract_roi_timeseries(
        functional_img=mock_functional_image,
        roi_masks=mock_roi_masks,
        output_dir=output_dir,
        participant_id="test_sub"
    )
    
    # Verify results exist
    assert "test_roi" in results, "Expected 'test_roi' in results"
    
    df = results["test_roi"]
    
    # Check that the number of rows matches the time dimension of the input image
    # Input image had 20 timepoints
    expected_timepoints = 20
    actual_timepoints = len(df)
    
    assert actual_timepoints == expected_timepoints, \
        f"Time series length ({actual_timepoints}) does not match input timepoints ({expected_timepoints})"
    
    # Verify column names
    assert "timepoint" in df.columns, "Expected 'timepoint' column"
    assert "test_roi_mean" in df.columns, "Expected 'test_roi_mean' column"
    
    # Verify saved file exists
    saved_file = output_dir / "sub-test_roi_timeseries.csv"
    assert saved_file.exists(), "Expected output CSV file to be saved"
    
    # Verify saved content matches memory content
    saved_df = df.read_csv(saved_file)
    assert len(saved_df) == expected_timepoints, "Saved file has incorrect number of rows"

def test_roi_extraction_empty_mask(tmp_path):
    """
    Test behavior when ROI mask is empty (no voxels).
    """
    shape = (10, 10, 10, 20)
    data = np.random.rand(*shape).astype(np.float32)
    affine = np.eye(4)
    func_img = nib.Nifti1Image(data, affine)
    
    empty_mask_data = np.zeros((10, 10, 10), dtype=np.int16)
    empty_mask_img = nib.Nifti1Image(empty_mask_data, affine)
    
    results = extract_roi_timeseries(
        functional_img=func_img,
        roi_masks={"empty_roi": empty_mask_img}
    )
    
    # Should return empty dataframe or handle gracefully
    # Depending on implementation, it might return 0 rows or skip
    # Here we expect it to run without crashing
    assert "empty_roi" in results or len(results) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
