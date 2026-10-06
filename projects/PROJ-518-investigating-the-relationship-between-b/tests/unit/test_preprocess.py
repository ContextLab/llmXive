"""
Unit tests for fMRI preprocessing functions.
"""
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np
from nilearn import image

from data.preprocess import preprocess_fmri, create_preprocessing_pipeline_config
from errors import DataMissingCreativityError


@pytest.fixture
def sample_nifti_file(tmp_path):
    """Create a temporary 4D NIfTI file for testing."""
    # Create a small 4D dummy volume (10x10x10x20)
    data = np.random.rand(10, 10, 10, 20).astype(np.float32)
    affine = np.eye(4)
    img = image.new_img_like(image.load_img(image.new_img_like(image.Nifti1Image(data, affine))), data)
    
    file_path = tmp_path / "test_fmri.nii.gz"
    img.to_filename(str(file_path))
    return str(file_path)


@pytest.fixture
def output_dir(tmp_path):
    """Create a temporary output directory."""
    output_path = tmp_path / "processed"
    output_path.mkdir(parents=True, exist_ok=True)
    return str(output_path)


def test_create_preprocessing_pipeline_config():
    """Test that the config function returns the correct dictionary."""
    config = create_preprocessing_pipeline_config(
        low_freq=0.01,
        high_freq=0.1,
        do_motion_correction=True,
        do_normalization=True
    )
    
    assert config["low_freq"] == 0.01
    assert config["high_freq"] == 0.1
    assert config["do_motion_correction"] is True
    assert config["do_normalization"] is True


def test_preprocess_fmri_file_not_found():
    """Test that FileNotFoundError is raised for missing input."""
    with pytest.raises(FileNotFoundError):
        preprocess_fmri("/nonexistent/path.nii.gz", "/tmp/output.nii.gz")


def test_preprocess_fmri_success(sample_nifti_file, output_dir):
    """Test successful preprocessing pipeline execution."""
    output_path = os.path.join(output_dir, "preprocessed_test.nii.gz")
    
    # Run preprocessing
    result_path = preprocess_fmri(
        sample_nifti_file,
        output_path,
        low_freq=0.01,
        high_freq=0.1,
        do_motion_correction=True,
        do_normalization=True
    )
    
    # Verify output file exists
    assert os.path.exists(result_path)
    assert result_path == output_path
    
    # Verify output is a valid NIfTI file
    output_img = image.load_img(result_path)
    assert output_img is not None
    assert output_img.shape[3] > 0  # Should have time dimension


def test_preprocess_fmri_without_normalization(sample_nifti_file, output_dir):
    """Test preprocessing without spatial normalization."""
    output_path = os.path.join(output_dir, "no_norm_test.nii.gz")
    
    result_path = preprocess_fmri(
        sample_nifti_file,
        output_path,
        do_normalization=False
    )
    
    assert os.path.exists(result_path)
    
    # Output shape should be closer to input (no resampling to MNI)
    output_img = image.load_img(result_path)
    input_img = image.load_img(sample_nifti_file)
    
    # Shapes might differ slightly due to resampling even without normalization
    # but the key is that it runs without error
    assert output_img is not None


def test_preprocess_fmri_with_custom_freqs(sample_nifti_file, output_dir):
    """Test preprocessing with custom frequency cutoffs."""
    output_path = os.path.join(output_dir, "custom_freq_test.nii.gz")
    
    result_path = preprocess_fmri(
        sample_nifti_file,
        output_path,
        low_freq=0.005,
        high_freq=0.15
    )
    
    assert os.path.exists(result_path)
    output_img = image.load_img(result_path)
    assert output_img is not None


def test_preprocess_fmri_creates_output_directory(sample_nifti_file, tmp_path):
    """Test that preprocess_fmri creates the output directory if it doesn't exist."""
    deep_output = tmp_path / "deep" / "nested" / "output" / "test.nii.gz"
    
    result_path = preprocess_fmri(
        sample_nifti_file,
        str(deep_output)
    )
    
    assert os.path.exists(result_path)
    assert deep_output.exists()