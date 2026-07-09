"""
Integration test for ROI extraction (User Story 1).

This test verifies that the ROI extraction pipeline correctly processes
preprocessed fMRI data and that the output dimensions match the expected
number of timepoints and ROIs.

It depends on:
- T001 (Directory structure)
- T002 (Dependencies)
- T004, T005, T006, T007, T008, T009 (Utilities)
- T010 (Data validation - ensures input data exists)
- T013 (Data download - ensures raw data exists)
- T014, T015, T016 (Preprocessing - ensures preprocessed data exists)
- T017 (ROI extraction implementation)
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import nibabel as nib
import nilearn
from nilearn import image, masking
from nilearn.input_data import NiftiLabelsMasker
from nilearn.datasets import load_mni152_template

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.io import load_json, save_json, ensure_dir
from code.utils.config import get_config, set_seed

# Constants for the test
EXPECTED_ROIS = ['dlPFC', 'ventral_striatum', 'ACC']
MIN_TIMEPOINTS = 50  # Minimum expected timepoints for a valid run
MAX_TIMEPOINTS = 500 # Maximum expected timepoints

@pytest.fixture(scope="module")
def config():
    """Load configuration for the test."""
    cfg = get_config()
    if cfg is None:
        # Set a default config if not loaded
        from code.utils.config import Config
        cfg = Config()
        cfg.data_dir = project_root / "data"
        cfg.processed_dir = cfg.data_dir / "processed"
        cfg.roi_dir = cfg.processed_dir / "roi"
        set_config(cfg)
    return cfg

@pytest.fixture(scope="module")
def sample_subject_id():
    """Get a sample subject ID from the downloaded data."""
    # This should be populated by T013 (data download)
    # We'll check for any subject in the raw data
    raw_dir = project_root / "data" / "raw" / "ds003694"
    if not raw_dir.exists():
        pytest.skip("Raw data not found. Please run data download (T013) first.")
    
    subjects = [d for d in raw_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]
    if not subjects:
        pytest.skip("No subject directories found in raw data.")
    
    return subjects[0].name

@pytest.fixture(scope="module")
def preprocessed_nifti_path(sample_subject_id, config):
    """Get path to preprocessed NIfTI file for the sample subject."""
    # Expected path from T014-T016 preprocessing pipeline
    preprocessed_dir = project_root / "data" / "processed" / "normalized"
    if not preprocessed_dir.exists():
        pytest.skip("Preprocessed data not found. Please run preprocessing (T014-T016) first.")
    
    # Look for the preprocessed file for this subject
    subject_dir = preprocessed_dir / sample_subject_id
    if not subject_dir.exists():
        pytest.skip(f"No preprocessed data for subject {sample_subject_id}")
    
    # Find the preprocessed NIfTI file
    nifti_files = list(subject_dir.glob("*.nii.gz"))
    if not nifti_files:
        pytest.skip(f"No NIfTI files found for subject {sample_subject_id}")
    
    return nifti_files[0]

@pytest.fixture(scope="module")
def roi_masks_path(config):
    """Get path to ROI masks (created by T017)."""
    roi_dir = config.roi_dir
    if not roi_dir.exists():
        pytest.skip("ROI directory not found. Please run ROI extraction setup (T017) first.")
    
    # Check if mask files exist
    mask_files = {}
    for roi in EXPECTED_ROIS:
        mask_file = roi_dir / f"{roi}_mask.nii.gz"
        if not mask_file.exists():
            pytest.skip(f"ROI mask {roi} not found. Please run ROI extraction (T017) first.")
        mask_files[roi] = mask_file
    
    return mask_files

def test_roi_extraction_dimensions(preprocessed_nifti_path, roi_masks_path, config):
    """
    Test that ROI extraction produces time series with correct dimensions.
    
    Verifies:
    1. The number of ROIs matches the expected count
    2. The number of timepoints in the output matches the input fMRI data
    3. The output contains no NaN values
    4. The output has reasonable value ranges (not all zeros or extreme values)
    """
    # Load the preprocessed fMRI data
    fmri_img = nib.load(str(preprocessed_nifti_path))
    fmri_data = fmri_img.get_fdata()
    fmri_shape = fmri_data.shape
    expected_timepoints = fmri_shape[3]  # 4D data: x, y, z, time
    
    # Verify the input has enough timepoints
    assert expected_timepoints >= MIN_TIMEPOINTS, \
        f"Input fMRI data has only {expected_timepoints} timepoints, expected at least {MIN_TIMEPOINTS}"
    assert expected_timepoints <= MAX_TIMEPOINTS, \
        f"Input fMRI data has {expected_timepoints} timepoints, expected at most {MAX_TIMEPOINTS}"
    
    # Extract time series for each ROI
    time_series_dict = {}
    for roi_name, mask_path in roi_masks_path.items():
        # Load the mask
        mask_img = nib.load(str(mask_path))
        
        # Create a NiftiLabelsMasker for this ROI
        # We use a simple approach: extract mean signal within the mask
        masker = NiftiLabelsMasker(
            labels_img=mask_img,
            standardize=False,
            detrend=False,
            low_pass=None,
            high_pass=None,
            t_r=2.0,  # Assume TR=2.0s if not specified
        )
        
        # Extract the time series
        try:
            ts = masker.fit_transform(fmri_img)
            time_series_dict[roi_name] = ts
        except Exception as e:
            pytest.fail(f"Failed to extract time series for {roi_name}: {str(e)}")
    
    # Verify we have time series for all expected ROIs
    assert len(time_series_dict) == len(EXPECTED_ROIS), \
        f"Expected {len(EXPECTED_ROIS)} ROIs, got {len(time_series_dict)}"
    
    # Verify dimensions for each ROI
    for roi_name, ts in time_series_dict.items():
        # ts should be (n_timepoints, 1) or (n_timepoints,)
        if ts.ndim == 1:
            n_timepoints = len(ts)
            n_rois = 1
        else:
            n_timepoints, n_rois = ts.shape
            assert n_rois == 1, f"Expected 1 ROI per extraction, got {n_rois}"
        
        # Check that timepoints match the input
        assert n_timepoints == expected_timepoints, \
            f"ROI {roi_name}: Expected {expected_timepoints} timepoints, got {n_timepoints}"
        
        # Check for NaN values
        assert not np.any(np.isnan(ts)), \
            f"ROI {roi_name}: Time series contains NaN values"
        
        # Check for reasonable value ranges
        ts_flat = ts.flatten()
        assert np.any(ts_flat != 0), \
            f"ROI {roi_name}: Time series is all zeros"
        assert np.std(ts_flat) > 1e-6, \
            f"ROI {roi_name}: Time series has no variance (std={np.std(ts_flat)})"
    
    # Save the results for inspection
    results = {
        "subject_id": Path(preprocessed_nifti_path).parent.name,
        "expected_timepoints": expected_timepoints,
        "rois": list(time_series_dict.keys()),
        "time_series_shapes": {k: v.shape for k, v in time_series_dict.items()},
        "all_checks_passed": True
    }
    
    output_dir = project_root / "data" / "processed" / "roi" / "test_results"
    ensure_dir(output_dir)
    output_file = output_dir / f"roi_extraction_test_{Path(preprocessed_nifti_path).stem}.json"
    save_json(results, str(output_file))
    
    print(f"ROI extraction test passed. Results saved to {output_file}")

def test_roi_extraction_consistency(preprocessed_nifti_path, roi_masks_path, config):
    """
    Test that ROI extraction is consistent across multiple runs.
    
    This test verifies that the same input produces the same output
    when the random seed is fixed.
    """
    set_seed(42)
    
    # First extraction
    time_series_1 = {}
    for roi_name, mask_path in roi_masks_path.items():
        mask_img = nib.load(str(mask_path))
        masker = NiftiLabelsMasker(
            labels_img=mask_img,
            standardize=False,
            detrend=False,
            low_pass=None,
            high_pass=None,
            t_r=2.0,
        )
        ts = masker.fit_transform(nib.load(str(preprocessed_nifti_path)))
        time_series_1[roi_name] = ts
    
    set_seed(42)
    
    # Second extraction
    time_series_2 = {}
    for roi_name, mask_path in roi_masks_path.items():
        mask_img = nib.load(str(mask_path))
        masker = NiftiLabelsMasker(
            labels_img=mask_img,
            standardize=False,
            detrend=False,
            low_pass=None,
            high_pass=None,
            t_r=2.0,
        )
        ts = masker.fit_transform(nib.load(str(preprocessed_nifti_path)))
        time_series_2[roi_name] = ts
    
    # Compare results
    for roi_name in time_series_1.keys():
        ts1 = time_series_1[roi_name]
        ts2 = time_series_2[roi_name]
        
        # Check that the results are identical (or very close)
        assert np.allclose(ts1, ts2, rtol=1e-5, atol=1e-8), \
            f"ROI {roi_name}: Results differ between runs"
    
    print("ROI extraction consistency test passed.")