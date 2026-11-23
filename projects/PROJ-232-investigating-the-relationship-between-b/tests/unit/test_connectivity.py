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

# Fixtures for testing
@pytest.fixture
def mock_time_series():
    """Generate a mock time series of shape (100, 5)."""
    np.random.seed(42)
    return np.random.randn(100, 5)

@pytest.fixture
def mock_atlas():
    """Create a temporary mock atlas file."""
    data = np.zeros((10, 10, 10), dtype=np.int32)
    data[2:4, 2:4, 2:4] = 1
    data[6:8, 6:8, 6:8] = 2
    # Create a NIfTI image
    img = nib.Nifti1Image(data, affine=np.eye(4))
    return img

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory for data."""
    return tmp_path

def test_compute_correlation_matrix_shape(mock_time_series):
    """Test that the correlation matrix has the correct shape."""
    corr_matrix = compute_correlation_matrix(mock_time_series)
    assert corr_matrix.shape == (5, 5)

def test_compute_correlation_matrix_symmetry(mock_time_series):
    """Test that the correlation matrix is symmetric."""
    corr_matrix = compute_correlation_matrix(mock_time_series)
    assert np.allclose(corr_matrix, corr_matrix.T)

def test_compute_correlation_matrix_diagonal(mock_time_series):
    """Test that the diagonal of the correlation matrix is 1."""
    corr_matrix = compute_correlation_matrix(mock_time_series)
    assert np.allclose(np.diag(corr_matrix), 1.0)

def test_compute_correlation_matrix_range(mock_time_series):
    """Test that correlation values are in [-1, 1]."""
    corr_matrix = compute_correlation_matrix(mock_time_series)
    assert corr_matrix.min() >= -1.0
    assert corr_matrix.max() <= 1.0

def test_validate_connectivity_matrix_valid(mock_time_series):
    """Test validation with a valid matrix."""
    corr_matrix = compute_correlation_matrix(mock_time_series)
    result = validate_connectivity_matrix(corr_matrix, "test_subject")
    assert result["is_symmetric"] is True
    assert result["is_diagonal_one"] is True
    assert result["in_range"] is True
    assert len(result["errors"]) == 0

def test_validate_connectivity_matrix_asymmetric():
    """Test validation with an asymmetric matrix."""
    matrix = np.array([[1.0, 0.5, 0.2],
                       [0.6, 1.0, 0.3],
                       [0.2, 0.3, 1.0]])
    with pytest.raises(ValueError, match="Matrix is not symmetric"):
        validate_connectivity_matrix(matrix, "test_subject")

def test_validate_connectivity_matrix_wrong_shape():
    """Test validation with a non-square matrix."""
    matrix = np.array([[1.0, 0.5],
                       [0.5, 1.0],
                       [0.2, 0.3]])
    result = validate_connectivity_matrix(matrix, "test_subject")
    assert result["is_symmetric"] is False
    assert len(result["errors"]) > 0

def test_validate_connectivity_matrix_out_of_range():
    """Test validation with values out of range."""
    matrix = np.array([[1.0, 1.5],
                       [1.5, 1.0]])
    with pytest.raises(ValueError, match="Values out of range"):
        validate_connectivity_matrix(matrix, "test_subject")

def test_load_schaefer_atlas(temp_data_dir):
    """Test loading the Schaefer atlas (mocked by creating a dummy file)."""
    # Create a dummy atlas file
    atlas_path = temp_data_dir / "Schaefer2018_200Parcels_7Networks_order_FSLMNI152_res-2.nii.gz"
    data = np.zeros((10, 10, 10), dtype=np.int32)
    data[2:4, 2:4, 2:4] = 1
    img = nib.Nifti1Image(data, affine=np.eye(4))
    nib.save(img, str(atlas_path))
    
    # Load it
    atlas_img, labels = load_schaefer_atlas(temp_data_dir)
    assert isinstance(atlas_img, nib.Nifti1Image)
    assert len(labels) == 1  # Only label 1 exists in mock

def test_extract_time_series(temp_data_dir, mock_atlas):
    """Test time series extraction (mocked)."""
    # Create a dummy fMRI image
    fmri_data = np.random.randn(10, 10, 10, 10)
    fmri_img = nib.Nifti1Image(fmri_data, affine=np.eye(4))
    
    # Save atlas
    atlas_path = temp_data_dir / "test_atlas.nii.gz"
    nib.save(mock_atlas, str(atlas_path))
    
    # Load atlas image for the function
    atlas_img_loaded = nib.load(str(atlas_path))
    
    # Extract
    ts = extract_time_series(atlas_img_loaded, fmri_img, ["ROI_1"])
    assert ts.shape[1] > 0  # Should have at least one time series

def test_process_subject(temp_data_dir, mock_atlas):
    """Test the full subject processing pipeline (mocked)."""
    # Setup paths
    atlas_dir = temp_data_dir / "atlas"
    atlas_dir.mkdir()
    
    # Save mock atlas
    atlas_path = atlas_dir / "Schaefer2018_200Parcels_7Networks_order_FSLMNI152_res-2.nii.gz"
    data = np.zeros((10, 10, 10), dtype=np.int32)
    data[2:4, 2:4, 2:4] = 1
    data[6:8, 6:8, 6:8] = 2
    img = nib.Nifti1Image(data, affine=np.eye(4))
    nib.save(img, str(atlas_path))
    
    # Create dummy fMRI
    fmri_data = np.random.randn(10, 10, 10, 20)
    fmri_img = nib.Nifti1Image(fmri_data, affine=np.eye(4))
    fmri_path = temp_data_dir / "sub-01_space-MNI_desc-preproc_bold.nii.gz"
    nib.save(fmri_img, str(fmri_path))
    
    # Process
    output_dir = temp_data_dir / "output"
    result = process_subject("sub-01", fmri_path, atlas_dir, output_dir)
    
    assert result["status"] == "success"
    assert Path(result["matrix_path"]).exists()