"""
Unit tests for the Nilearn lightweight preprocessing fallback module.

These tests verify that the nilearn_fallback module functions correctly
without requiring fMRIPrep or Docker.
"""

import os
import tempfile
import numpy as np
import nibabel as nib
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.preprocessing.nilearn_fallback import (
    NilearnFallbackError,
    get_nilearn_config,
    load_bold_image,
    motion_correction,
    slice_timing_correction,
    normalize_to_mni152,
    smooth_image,
    bandpass_filter,
    preprocess_bold,
    run_preprocessing_pipeline
)


@pytest.fixture
def temp_nifti_file():
    """Create a temporary NIfTI file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as f:
        # Create a simple 4D image (3x3x3 voxels, 10 timepoints)
        data = np.random.randn(3, 3, 3, 10).astype(np.float32)
        affine = np.eye(4)
        img = nib.Nifti1Image(data, affine)
        nib.save(img, f.name)
        yield f.name
        os.unlink(f.name)


@pytest.fixture
def temp_input_dir():
    """Create a temporary directory with test NIfTI files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a few test files
        for i in range(3):
            path = Path(tmpdir) / f"sub-{i:02d}_task-rest_bold.nii.gz"
            data = np.random.randn(3, 3, 3, 10).astype(np.float32)
            affine = np.eye(4)
            img = nib.Nifti1Image(data, affine)
            nib.save(img, str(path))
        yield tmpdir


class TestGetNilearnConfig:
    """Tests for get_nilearn_config function."""

    def test_default_config(self):
        """Test that default config returns expected values."""
        config = get_nilearn_config()
        
        assert 'smoothing_mm' in config
        assert config['smoothing_mm'] == 6
        assert 'bandpass_range' in config
        assert config['bandpass_range'] == (0.01, 0.1)
        assert config['standardize'] is True
        assert config['detrend'] is True


class TestLoadBoldImage:
    """Tests for load_bold_image function."""

    def test_load_valid_image(self, temp_nifti_file):
        """Test loading a valid NIfTI file."""
        img = load_bold_image(temp_nifti_file)
        assert isinstance(img, nib.Nifti1Image)
        assert img.shape[3] == 10  # Check time dimension

    def test_load_missing_file(self):
        """Test that loading a missing file raises an error."""
        with pytest.raises(NilearnFallbackError):
            load_bold_image("/nonexistent/path/file.nii.gz")


class TestMotionCorrection:
    """Tests for motion_correction function."""

    def test_motion_correction_passes_through(self, temp_nifti_file):
        """Test that motion_correction returns the input image."""
        img = load_bold_image(temp_nifti_file)
        result = motion_correction(img)
        assert isinstance(result, nib.Nifti1Image)
        # Since we don't do full realignment, shape should be preserved
        assert result.shape == img.shape


class TestSliceTimingCorrection:
    """Tests for slice_timing_correction function."""

    def test_slice_timing_passes_through(self, temp_nifti_file):
        """Test that slice_timing_correction returns the input image."""
        img = load_bold_image(temp_nifti_file)
        result = slice_timing_correction(img)
        assert isinstance(result, nib.Nifti1Image)
        assert result.shape == img.shape


class TestNormalizeToMNI152:
    """Tests for normalize_to_mni152 function."""

    @patch('nilearn.datasets.load_mni152_template')
    def test_normalize_to_mni(self, mock_template, temp_nifti_file):
        """Test normalization to MNI152 space."""
        # Mock the template
        mock_data = np.random.randn(10, 10, 10).astype(np.float32)
        mock_affine = np.eye(4)
        mock_template.return_value = nib.Nifti1Image(mock_data, mock_affine)
        
        img = load_bold_image(temp_nifti_file)
        result = normalize_to_mni152(img)
        
        assert isinstance(result, nib.Nifti1Image)
        # After resampling, shape should change
        assert len(result.shape) == 4


class TestSmoothImage:
    """Tests for smooth_image function."""

    def test_smoothing_applies(self, temp_nifti_file):
        """Test that smoothing is applied."""
        img = load_bold_image(temp_nifti_file)
        result = smooth_image(img, fwhm=6.0)
        
        assert isinstance(result, nib.Nifti1Image)
        # Shape should be preserved
        assert result.shape == img.shape


class TestBandpassFilter:
    """Tests for bandpass_filter function."""

    def test_bandpass_filter_applies(self, temp_nifti_file):
        """Test that bandpass filtering is applied."""
        img = load_bold_image(temp_nifti_file)
        result = bandpass_filter(img, low_freq=0.01, high_freq=0.1, t_r=2.0)
        
        assert isinstance(result, nib.Nifti1Image)
        assert result.shape == img.shape


class TestPreprocessBold:
    """Tests for the full preprocess_bold pipeline."""

    def test_full_pipeline(self, temp_nifti_file):
        """Test the complete preprocessing pipeline."""
        with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as out_file:
            out_path = out_file.name
        
        try:
            result = preprocess_bold(temp_nifti_file, out_path)
            
            assert result['status'] == 'success'
            assert result['input_path'] == temp_nifti_file
            assert result['output_path'] == out_path
            assert os.path.exists(out_path)
        finally:
            if os.path.exists(out_path):
                os.unlink(out_path)


class TestRunPreprocessingPipeline:
    """Tests for the batch preprocessing pipeline."""

    def test_batch_processing(self, temp_input_dir):
        """Test processing multiple files in a directory."""
        with tempfile.TemporaryDirectory() as out_dir:
            results = run_preprocessing_pipeline(temp_input_dir, out_dir)
            
            assert len(results) == 3
            for r in results:
                assert r['status'] == 'success'
                assert os.path.exists(r['output_path'])
