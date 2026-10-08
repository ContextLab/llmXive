"""
Unit tests for Nilearn fallback preprocessing pipeline.
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
    data = np.random.rand(10, 10, 10, 5)  # Small 4D image
    affine = np.eye(4)
    img = nib.Nifti1Image(data, affine)

    with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as f:
        nib.save(img, f.name)
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def temp_input_dir():
    """Create a temporary directory with test NIfTI files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a few test files
        for i in range(3):
            data = np.random.rand(5, 5, 5, 3)
            affine = np.eye(4)
            img = nib.Nifti1Image(data, affine)
            path = os.path.join(tmpdir, f'test_{i}.nii.gz')
            nib.save(img, path)
        yield tmpdir


class TestGetNilearnConfig:
    def test_get_config_returns_dict(self):
        config = get_nilearn_config()
        assert isinstance(config, dict)
        assert 'motion_correction' in config
        assert 'smoothing_mm' in config

    def test_default_values(self):
        config = get_nilearn_config()
        assert config['smoothing_mm'] == 6
        assert config['bandpass_range'] == (0.01, 0.1)


class TestLoadBoldImage:
    def test_load_existing_file(self, temp_nifti_file):
        img = load_bold_image(temp_nifti_file)
        assert isinstance(img, nib.Nifti1Image)
        assert img.shape[3] == 5

    def test_load_nonexistent_file(self):
        with pytest.raises(NilearnFallbackError):
            load_bold_image("/nonexistent/path/file.nii.gz")


class TestMotionCorrection:
    def test_motion_correction_returns_image(self, temp_nifti_file):
        img = load_bold_image(temp_nifti_file)
        corrected = motion_correction(img)
        assert isinstance(corrected, nib.Nifti1Image)
        assert corrected.shape == img.shape


class TestSliceTimingCorrection:
    def test_slice_timing_returns_image(self, temp_nifti_file):
        img = load_bold_image(temp_nifti_file)
        corrected = slice_timing_correction(img, tr=2.0)
        assert isinstance(corrected, nib.Nifti1Image)
        assert corrected.shape == img.shape


class TestNormalizeToMNI152:
    @patch('nilearn.datasets.load_mni152_template')
    @patch('nilearn.image.resample_to_img')
    def test_normalize_returns_image(self, mock_resample, mock_load_template, temp_nifti_file):
        # Mock the dependencies
        mock_template = MagicMock()
        mock_load_template.return_value = mock_template

        mock_resampled = MagicMock()
        mock_resample.return_value = mock_resampled

        img = load_bold_image(temp_nifti_file)
        normalized = normalize_to_mni152(img)

        mock_load_template.assert_called_once()
        mock_resample.assert_called_once()
        assert normalized == mock_resampled


class TestSmoothImage:
    @patch('nilearn.image.smooth_img')
    def test_smooth_returns_image(self, mock_smooth, temp_nifti_file):
        mock_smoothed = MagicMock()
        mock_smooth.return_value = mock_smoothed

        img = load_bold_image(temp_nifti_file)
        smoothed = smooth_image(img, fwhm=6.0)

        mock_smooth.assert_called_once()
        assert smoothed == mock_smoothed


class TestBandpassFilter:
    def test_bandpass_returns_image(self, temp_nifti_file):
        img = load_bold_image(temp_nifti_file)
        filtered = bandpass_filter(img, t_r=2.0, low_pass=0.1, high_pass=0.01)
        assert isinstance(filtered, nib.Nifti1Image)
        assert filtered.shape == img.shape


class TestPreprocessBold:
    @patch('src.preprocessing.nilearn_fallback.motion_correction')
    @patch('src.preprocessing.nilearn_fallback.slice_timing_correction')
    @patch('src.preprocessing.nilearn_fallback.normalize_to_mni152')
    @patch('src.preprocessing.nilearn_fallback.smooth_image')
    @patch('src.preprocessing.nilearn_fallback.bandpass_filter')
    def test_preprocess_bold_calls_all_steps(self, mock_bandpass, mock_smooth, mock_norm,
                                             mock_slice, mock_motion, temp_nifti_file):
        # Setup mocks
        mock_motion.return_value = MagicMock()
        mock_slice.return_value = MagicMock()
        mock_norm.return_value = MagicMock()
        mock_smooth.return_value = MagicMock()
        mock_bandpass.return_value = MagicMock()

        with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as f:
            out_path = f.name

        try:
            result = preprocess_bold(temp_nifti_file, out_path)
            assert result is True
            assert mock_motion.called
            assert mock_slice.called
            assert mock_norm.called
            assert mock_smooth.called
            assert mock_bandpass.called
        finally:
            if os.path.exists(out_path):
                os.unlink(out_path)


class TestRunPreprocessingPipeline:
    def test_pipeline_processes_directory(self, temp_input_dir):
        with tempfile.TemporaryDirectory() as out_dir:
            results = run_preprocessing_pipeline(temp_input_dir, out_dir)
            assert len(results) == 3
            for r in results:
                assert os.path.exists(r)
                assert r.startswith(out_dir)

    def test_pipeline_no_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with tempfile.TemporaryDirectory() as out_dir:
                results = run_preprocessing_pipeline(tmpdir, out_dir, "*.nii.gz")
                assert len(results) == 0