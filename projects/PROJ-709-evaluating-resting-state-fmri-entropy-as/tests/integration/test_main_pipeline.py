"""
Integration test for the main pipeline (T018a).

This test verifies that code/main.py correctly orchestrates the subject loop,
skips excluded subjects, and generates the expected output CSV file.
"""
import os
import sys
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from main import load_valid_subjects, load_exclusions, process_single_subject, main
from utils import setup_logger

@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project structure for testing."""
    # Create directory structure
    data_raw = tmp_path / "data" / "raw"
    data_processed = tmp_path / "data" / "processed"
    data_derived = tmp_path / "data" / "derived"
    
    data_raw.mkdir(parents=True)
    data_processed.mkdir(parents=True)
    data_derived.mkdir(parents=True)
    
    # Create mock valid_subjects.csv
    valid_subjects_data = [
        {"subject_id": "sub-01", "nifti_path": str(data_processed / "scrubbed_sub-01.nii.gz")},
        {"subject_id": "sub-02", "nifti_path": str(data_processed / "scrubbed_sub-02.nii.gz")},
        {"subject_id": "sub-03", "nifti_path": str(data_processed / "scrubbed_sub-03.nii.gz")},
    ]
    valid_df = pd.DataFrame(valid_subjects_data)
    valid_df.to_csv(data_derived / "valid_subjects.csv", index=False)
    
    # Create mock exclusions.log
    with open(data_raw / "exclusions.log", "w") as f:
        f.write("subject_id,reason,fd_mean\n")
        f.write("sub-02,Low volumes,0.3\n")  # sub-02 should be excluded
    
    # Create mock scrubbed NIfTI files (using numpy to create a simple nifti)
    # We need nibabel for this
    try:
        import nibabel as nib
        for i in range(1, 4):
            subject_id = f"sub-{i:02d}"
            # Create a dummy 4D image: (x, y, z, time)
            # 2x2x2 voxels, 120 time points
            data = np.random.rand(2, 2, 2, 120).astype(np.float32)
            img = nib.Nifti1Image(data, np.eye(4))
            nib.save(img, data_processed / f"scrubbed_{subject_id}.nii.gz")
    except ImportError:
        pytest.skip("nibabel not installed, skipping NIfTI creation")
    
    return tmp_path

def test_load_valid_subjects(temp_project_dir):
    """Test loading valid subjects from CSV."""
    # Temporarily override the path in the module
    import main
    original_derived = main.DATA_DERIVED_DIR
    main.DATA_DERIVED_DIR = temp_project_dir / "data" / "derived"
    
    try:
        subjects = load_valid_subjects()
        assert len(subjects) == 3
        assert subjects[0]['subject_id'] == 'sub-01'
    finally:
        main.DATA_DERIVED_DIR = original_derived

def test_load_exclusions(temp_project_dir):
    """Test loading exclusions from log."""
    import main
    original_raw = main.DATA_RAW_DIR
    main.DATA_RAW_DIR = temp_project_dir / "data" / "raw"
    
    try:
        exclusions = load_exclusions()
        assert 'sub-02' in exclusions
        assert 'sub-01' not in exclusions
    finally:
        main.DATA_RAW_DIR = original_raw

def test_process_single_subject_skips_excluded(temp_project_dir):
    """Test that excluded subjects are skipped."""
    import main
    original_raw = main.DATA_RAW_DIR
    main.DATA_RAW_DIR = temp_project_dir / "data" / "raw"
    
    try:
        exclusions = load_exclusions()
        sub02_info = {"subject_id": "sub-02", "nifti_path": "dummy"}
        
        result = process_single_subject(sub02_info, exclusions)
        assert result is None
    finally:
        main.DATA_RAW_DIR = original_raw

def test_main_generates_output(temp_project_dir):
    """Test that main() generates the output CSV."""
    import main
    original_raw = main.DATA_RAW_DIR
    original_processed = main.DATA_PROCESSED_DIR
    original_derived = main.DATA_DERIVED_DIR
    
    main.DATA_RAW_DIR = temp_project_dir / "data" / "raw"
    main.DATA_PROCESSED_DIR = temp_project_dir / "data" / "processed"
    main.DATA_DERIVED_DIR = temp_project_dir / "data" / "derived"
    
    # Mock the entropy computation to avoid heavy dependencies in this test
    # We will patch compute_entropy_features to return dummy values
    try:
        from unittest.mock import patch
        
        def mock_compute_entropy_features(time_series_data, m, r_factor):
            # Return a list of dummy entropy values (200 parcels)
            return [0.5] * 200
        
        with patch('main.compute_entropy_features', side_effect=mock_compute_entropy_features):
            # Also need to mock load_scrubbed_subject and truncate_time_series
            def mock_load_scrubbed_subject(path):
                return np.random.rand(2, 2, 2, 120)
            
            def mock_truncate_time_series(data, target_length):
                return data[:, :, :, :target_length]
            
            with patch('main.load_scrubbed_subject', side_effect=mock_load_scrubbed_subject):
                with patch('main.truncate_time_series', side_effect=mock_truncate_time_series):
                    ret_code = main.main()
                    
                    assert ret_code == 0
                    
                    # Check output file
                    output_path = main.OUTPUT_CSV_PATH
                    assert output_path.exists(), f"Output file {output_path} was not created"
                    
                    df = pd.read_csv(output_path)
                    # Should have 2 subjects (sub-01 and sub-03, sub-02 excluded)
                    assert len(df) == 2, f"Expected 2 rows, got {len(df)}"
                    assert 'subject_id' in df.columns
                    assert 'parcel_0' in df.columns
                    
                    # Check for NaN
                    assert not df.isnull().any().any(), "Output contains NaN values"
                    
    except Exception as e:
        pytest.fail(f"Test failed with exception: {e}")
    finally:
        main.DATA_RAW_DIR = original_raw
        main.DATA_PROCESSED_DIR = original_processed
        main.DATA_DERIVED_DIR = original_derived

if __name__ == "__main__":
    pytest.main([__file__, "-v"])