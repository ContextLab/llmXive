"""
Integration Test for ROI Extraction.
Verifies that ROI time-series dimensions match the number of timepoints in the fMRI data.
"""
import os
import tempfile
from pathlib import Path
import numpy as np
import nibabel as nib
import pandas as pd
import pytest

from preprocessing.roi_extraction import load_roi_masks, extract_roi_timeseries
from utils.io import save_csv

@pytest.fixture
def temp_roi_data(tmp_path):
    """
    Creates a temporary directory with dummy fMRI data and ROI masks.
    """
    root = tmp_path / "roi_test"
    root.mkdir()
    
    # Create dummy functional data (4D NIfTI: X, Y, Z, Time)
    # Dimensions: 10x10x10 volume, 50 timepoints
    shape = (10, 10, 10, 50)
    data = np.random.rand(*shape).astype(np.float32)
    affine = np.eye(4)
    nii_img = nib.Nifti1Image(data, affine)
    
    func_dir = root / "func"
    func_dir.mkdir()
    func_file = func_dir / "sub-01_ses-01_task-social_bold.nii.gz"
    nib.save(nii_img, str(func_file))
    
    # Create dummy ROI masks
    # We need masks that align with the functional data
    # Mask 1: dlPFC (first few voxels)
    mask_data = np.zeros(shape[:3], dtype=np.uint8)
    mask_data[0:2, 0:2, 0:2] = 1
    mask_img = nib.Nifti1Image(mask_data, affine)
    
    roi_dir = root / "masks"
    roi_dir.mkdir()
    
    mask_file_1 = roi_dir / "dlPFC_mask.nii.gz"
    nib.save(mask_img, str(mask_file_1))
    
    # Mask 2: Ventral Striatum
    mask_data_2 = np.zeros(shape[:3], dtype=np.uint8)
    mask_data_2[5:7, 5:7, 5:7] = 1
    mask_img_2 = nib.Nifti1Image(mask_data_2, affine)
    mask_file_2 = roi_dir / "vStriatum_mask.nii.gz"
    nib.save(mask_img_2, str(mask_file_2))
    
    return str(root), shape[3], list(mask_file_1.parent.glob("*.nii.gz"))

def test_roi_extraction_dimensions(temp_roi_data):
    """
    Integration test: Verify that extracted ROI time-series have the correct length
    matching the number of timepoints in the original fMRI data.
    """
    root, expected_timepoints, mask_files = temp_roi_data
    func_file = root / "func" / "sub-01_ses-01_task-social_bold.nii.gz"
    
    # Load masks
    masks = load_roi_masks(mask_files)
    assert len(masks) == 2, "Should load 2 masks"
    
    # Extract time series
    # We pass the func file and the list of mask paths
    roi_timeseries = extract_roi_timeseries(str(func_file), mask_files)
    
    # roi_timeseries should be a dict: {mask_name: np.array}
    # or a list of arrays? Let's check the implementation expectation.
    # Assuming it returns a dict or list of arrays where each array is (Timepoints, ROIs) or (Timepoints,)
    # The function extract_roi_timeseries in the API surface is expected to return data.
    
    # Check that we got results
    assert roi_timeseries is not None
    
    # If it's a dict
    if isinstance(roi_timeseries, dict):
        for roi_name, ts in roi_timeseries.items():
            # ts should be 1D array of shape (Timepoints,)
            assert isinstance(ts, np.ndarray), f"ROI {roi_name} time-series must be numpy array"
            assert ts.ndim == 1, f"ROI {roi_name} time-series must be 1D"
            assert ts.shape[0] == expected_timepoints, \
                f"ROI {roi_name} time-series length {ts.shape[0]} does not match expected {expected_timepoints}"
    elif isinstance(roi_timeseries, list):
        for i, ts in enumerate(roi_timeseries):
            assert isinstance(ts, np.ndarray)
            assert ts.ndim == 1
            assert ts.shape[0] == expected_timepoints, \
                f"ROI {i} time-series length {ts.shape[0]} does not match expected {expected_timepoints}"
    else:
        pytest.fail(f"Unexpected return type from extract_roi_timeseries: {type(roi_timeseries)}")
    
    # Verify data is not all zeros (dummy data has random values)
    if isinstance(roi_timeseries, dict):
        for ts in roi_timeseries.values():
            assert not np.all(ts == 0), "Extracted time-series should not be all zeros"
    elif isinstance(roi_timeseries, list):
        for ts in roi_timeseries:
            assert not np.all(ts == 0)
