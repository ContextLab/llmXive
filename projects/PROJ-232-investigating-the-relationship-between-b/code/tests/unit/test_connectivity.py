import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import nibabel as nib

from src.analysis.connectivity import (
    compute_correlation_matrix,
    validate_connectivity_matrix,
    load_schaefer_atlas,
    extract_time_series,
    process_subject
)

@pytest.fixture
def mock_time_series():
    """Create mock time series data (100 timepoints, 200 regions)."""
    np.random.seed(42)
    return np.random.randn(100, 200)

@pytest.fixture
def mock_atlas():
    """Create a mock Schaefer atlas (2mm, 200 parcels)."""
    # Create a 91x109x91 volume (MNI 2mm)
    shape = (91, 109, 91)
    data = np.zeros(shape, dtype=np.int16)
    
    # Assign parcel IDs 1-200 in a simple pattern
    parcel_id = 1
    for i in range(shape[0]):
        for j in range(shape[1]):
            for k in range(shape[2]):
                if parcel_id <= 200:
                    data[i, j, k] = parcel_id
                    parcel_id += 1
                else:
                    break
            if parcel_id > 200:
                break
        if parcel_id > 200:
            break
    
    # Create NIfTI image
    affine = np.eye(4)
    affine[0, 0] = 2.0
    affine[1, 1] = 2.0
    affine[2, 2] = 2.0
    affine[0, 3] = -90.0
    affine[1, 3] = -126.0
    affine[2, 3] = -72.0
    
    img = nib.Nifti1Image(data, affine)
    labels = [f"Parcel_{i}" for i in range(1, 201)]
    
    return img, labels

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary data directory."""
    return tmp_path

def test_compute_correlation_matrix_shape(mock_time_series):
    """Test that correlation matrix has correct shape."""
    corr = compute_correlation_matrix(mock_time_series)
    assert corr.shape == (200, 200)

def test_compute_correlation_matrix_symmetry(mock_time_series):
    """Test that correlation matrix is symmetric."""
    corr = compute_correlation_matrix(mock_time_series)
    assert np.allclose(corr, corr.T)

def test_compute_correlation_matrix_diagonal(mock_time_series):
    """Test that correlation matrix diagonal is 1."""
    corr = compute_correlation_matrix(mock_time_series)
    assert np.allclose(np.diag(corr), 1.0)

def test_compute_correlation_matrix_range(mock_time_series):
    """Test that correlation values are in [-1, 1]."""
    corr = compute_correlation_matrix(mock_time_series)
    assert np.all(corr >= -1.0) and np.all(corr <= 1.0)

def test_validate_connectivity_matrix_valid(mock_time_series):
    """Test validation passes for valid matrix."""
    corr = compute_correlation_matrix(mock_time_series)
    labels = [f"Parcel_{i}" for i in range(1, 201)]
    
    validation = validate_connectivity_matrix(corr, labels)
    
    assert validation["is_valid"] is True
    assert validation["shape_correct"] is True
    assert validation["is_symmetric"] is True
    assert validation["diagonal_is_one"] is True
    assert validation["values_in_range"] is True

def test_validate_connectivity_matrix_asymmetric(mock_time_series):
    """Test validation fails for asymmetric matrix."""
    corr = compute_correlation_matrix(mock_time_series)
    # Make it asymmetric
    corr[0, 1] = 0.5
    corr[1, 0] = 0.8
    
    labels = [f"Parcel_{i}" for i in range(1, 201)]
    validation = validate_connectivity_matrix(corr, labels)
    
    assert validation["is_valid"] is False
    assert validation["is_symmetric"] is False

def test_validate_connectivity_matrix_wrong_shape(mock_time_series):
    """Test validation fails for wrong shape."""
    corr = compute_correlation_matrix(mock_time_series)
    # Wrong labels count
    labels = [f"Parcel_{i}" for i in range(1, 101)]  # Only 100 labels
    
    validation = validate_connectivity_matrix(corr, labels)
    
    assert validation["is_valid"] is False
    assert validation["shape_correct"] is False

def test_validate_connectivity_matrix_out_of_range(mock_time_series):
    """Test validation fails for out-of-range values."""
    corr = compute_correlation_matrix(mock_time_series)
    # Add out-of-range value
    corr[0, 0] = 1.5
    
    labels = [f"Parcel_{i}" for i in range(1, 201)]
    validation = validate_connectivity_matrix(corr, labels)
    
    assert validation["is_valid"] is False
    assert validation["values_in_range"] is False

def test_load_schaefer_atlas(tmp_path):
    """Test that Schaefer atlas loads correctly."""
    # This test will download the atlas if not cached
    # For CI, we might want to mock this, but for now test the function exists
    cache_dir = tmp_path / "cache"
    atlas_img, labels = load_schaefer_atlas(cache_dir)
    
    assert atlas_img is not None
    assert isinstance(labels, list)
    assert len(labels) == 200

def test_extract_time_series(tmp_path, mock_atlas):
    """Test time series extraction."""
    # Create a mock fMRI image
    shape = (91, 109, 91, 50)  # 50 timepoints
    data = np.random.randn(*shape)
    affine = np.eye(4)
    affine[0, 0] = 2.0
    affine[1, 1] = 2.0
    affine[2, 2] = 2.0
    
    fmri_img = nib.Nifti1Image(data, affine)
    fmri_path = tmp_path / "mock_fmri.nii.gz"
    nib.save(fmri_img, fmri_path)
    
    atlas_img, labels = mock_atlas
    
    time_series = extract_time_series(fmri_path, atlas_img, labels)
    
    assert time_series.shape == (50, 200)

def test_process_subject(tmp_path, mock_atlas):
    """Test full subject processing pipeline."""
    # Create a mock fMRI image
    shape = (91, 109, 91, 50)
    data = np.random.randn(*shape)
    affine = np.eye(4)
    affine[0, 0] = 2.0
    affine[1, 1] = 2.0
    affine[2, 2] = 2.0
    
    fmri_img = nib.Nifti1Image(data, affine)
    fmri_path = tmp_path / "sub-01_task-rest_preproc.nii.gz"
    nib.save(fmri_img, fmri_path)
    
    output_dir = tmp_path / "connectivity"
    cache_dir = tmp_path / "cache"
    
    # Mock load_schaefer_atlas to return our mock atlas
    import src.analysis.connectivity as conn_module
    original_load = conn_module.load_schaefer_atlas
    
    def mock_load(cache_dir=None):
        return mock_atlas
    
    conn_module.load_schaefer_atlas = mock_load
    
    try:
        result = process_subject(
            subject_id="sub-01",
            fmri_path=fmri_path,
            output_dir=output_dir,
            cache_dir=cache_dir
        )
        
        assert result["subject_id"] == "sub-01"
        assert result["success"] is True
        assert result["matrix_shape"] == [200, 200]
        
        # Check output files exist
        assert (output_dir / "sub-01_connectivity.npy").exists()
        assert (output_dir / "sub-01_labels.json").exists()
        assert (output_dir / "sub-01_validation.json").exists()
        assert (output_dir / "sub-01_results.json").exists()
    finally:
        conn_module.load_schaefer_atlas = original_load