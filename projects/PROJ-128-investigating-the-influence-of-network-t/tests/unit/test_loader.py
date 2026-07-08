"""
Unit tests for data loading utilities.
These tests verify the logic of the loader without requiring real data files
to be present in the environment (mocking the file system).
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import nibabel as nib
import tempfile
import os

from code.preprocess.loader import (
    _get_raw_data_dir,
    _validate_data_existence,
    load_hcp_dmri,
    load_hcp_fmri,
)
from code.config import CONFIG

@pytest.fixture
def mock_data_dir(tmp_path):
    """Create a temporary directory structure mimicking HCP data."""
    raw_dir = tmp_path / "raw" / "hcp" / "100307"
    raw_dir.mkdir(parents=True)
    
    # Create dummy NIfTI files
    # dMRI
    dmri_data = np.random.rand(10, 10, 10, 5).astype(np.float32)
    dmri_img = nib.Nifti1Image(dmri_data, np.eye(4))
    dmri_path = raw_dir / "100307_dMRI.nii.gz"
    nib.save(dmri_img, str(dmri_path))
    
    # bvals
    bvals = np.array([0, 1000, 1000, 1000, 2000])
    np.savetxt(str(raw_dir / "100307_dMRI.bval"), bvals)
    
    # fMRI
    fmri_data = np.random.rand(10, 10, 10, 20).astype(np.float32)
    fmri_img = nib.Nifti1Image(fmri_data, np.eye(4))
    fmri_path = raw_dir / "100307_rfMRI_REST1_LR.nii.gz"
    nib.save(fmri_img, str(fmri_path))
    
    return tmp_path

def test_get_raw_data_dir():
    """Test that the raw data directory path is constructed correctly."""
    raw_dir = _get_raw_data_dir()
    assert "raw" in str(raw_dir)
    assert "hcp" in str(raw_dir)

def test_validate_data_existence_missing(tmp_path):
    """Test validation fails when directory is empty."""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    assert _validate_data_existence(empty_dir) is False

def test_validate_data_existence_present(mock_data_dir):
    """Test validation passes when data is present."""
    raw_dir = mock_data_dir / "raw" / "hcp"
    assert _validate_data_existence(raw_dir) is True

@patch('code.preprocess.loader._get_raw_data_dir')
@patch('code.preprocess.loader._validate_data_existence', return_value=True)
def test_load_hcp_dmri_success(mock_validate, mock_get_dir, mock_data_dir):
    """Test successful loading of dMRI data."""
    # Mock the path to point to our temp fixture
    mock_get_dir.return_value = mock_data_dir / "raw" / "hcp"
    
    data, bvals = load_hcp_dmri("100307")
    
    assert data.shape[3] == 5  # 5 volumes
    assert len(bvals) == 5
    assert np.array_equal(bvals, [0, 1000, 1000, 1000, 2000])

@patch('code.preprocess.loader._get_raw_data_dir')
@patch('code.preprocess.loader._validate_data_existence', return_value=True)
def test_load_hcp_fmri_success(mock_validate, mock_get_dir, mock_data_dir):
    """Test successful loading of fMRI data."""
    mock_get_dir.return_value = mock_data_dir / "raw" / "hcp"
    
    data = load_hcp_fmri("100307")
    
    assert data.shape[3] == 20  # 20 timepoints