"""
Unit tests for the Nilearn fallback preprocessing module.
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
    """Create a temporary 4D NIfTI file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as f:
        # Create a simple 4D image (10x10x10x5)
        data = np.random.randn(10, 10, 10, 5).astype(np.float32)
        affine = np.eye(4)
        img = nib.Nifti1Image(data, affine)
        nib.save(img, f.name)
        yield Path(f.name)
        os.unlink(f.name)


@pytest.fixture
def temp_input_dir():
    """Create a temporary directory with test NIfTI files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test files
        for i in range(2):
            filepath = tmpdir / f"sub-{i+1}_task-rest_bold.nii.gz"
            data = np.random.randn(10, 10, 10, 5).astype(np.float32)
            affine = np.eye(4)
            img = nib.Nifti1Image(data, affine)
            nib.save(img, str(filepath))
        
        yield tmpdir


class TestGetNilearnConfig:
    def test_get_config_returns_dict(self):
        """Test that get_nilearn_config returns a dictionary."""
        config = get_nilearn_config()
        assert isinstance(config, dict)
        assert 'motion_correction' in config
        assert 'smoothing_mm' in config
        assert 'bandpass_range' in config

    def test_default_smoothing_is_6mm(self):
        """Test that default smoothing is 6mm."""
        config = get_nilearn_config()
        assert config['smoothing_mm'] == 6

    def test_default_bandpass_range(self):
        """Test that default bandpass range is (0.01, 0.1)."""
        config = get_nilearn_config()
        assert config['bandpass_range'] == (0.01, 0.1)


class TestLoadBoldImage:
    def test_load_valid_image(self, temp_nifti_file):
        """Test loading a valid 4D NIfTI image."""
        img = load_bold_image(temp_nifti_file)
        assert isinstance(img, nib.Nifti1Image)
        assert len(img.shape) == 4

    def test_load_nonexistent_file(self):
        """Test that loading a non-existent file raises an error."""
        with pytest.raises(NilearnFallbackError):
            load_bold_image(Path('/nonexistent/file.nii.gz'))

    def test_load_3d_image_raises_error(self):
        """Test that loading a 3D image raises an error."""
        with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as f:
            data = np.random.randn(10, 10, 10).astype(np.float32)
            affine = np.eye(4)
            img = nib.Nifti1Image(data, affine)
            nib.save(img, f.name)
            filepath = Path(f.name)
        
        try:
            with pytest.raises(NilearnFallbackError):
                load_bold_image(filepath)
        finally:
            os.unlink(filepath)


class TestMotionCorrection:
    def test_motion_correction_returns_image(self, temp_nifti_file):
        """Test that motion correction returns a valid image."""
        img = load_bold_image(temp_nifti_file)
        corrected = motion_correction(img)
        assert isinstance(corrected, nib.Nifti1Image)
        assert corrected.shape == img.shape

    def test_motion_correction_preserves_data(self, temp_nifti_file):
        """Test that motion correction preserves data shape."""
        img = load_bold_image(temp_nifti_file)
        original_data = img.get_fdata()
        corrected = motion_correction(img)
        corrected_data = corrected.get_fdata()
        assert original_data.shape == corrected_data.shape


class TestSliceTimingCorrection:
    def test_slice_timing_correction_returns_image(self, temp_nifti_file):
        """Test that slice timing correction returns a valid image."""
        img = load_bold_image(temp_nifti_file)
        corrected = slice_timing_correction(img, TR=2.0)
        assert isinstance(corrected, nib.Nifti1Image)
        assert corrected.shape == img.shape

    def test_slice_timing_with_explicit_tr(self, temp_nifti_file):
        """Test slice timing correction with explicit TR."""
        img = load_bold_image(temp_nifti_file)
        corrected = slice_timing_correction(img, TR=2.5, reference_slice=0)
        assert isinstance(corrected, nib.Nifti1Image)


class TestNormalizeToMNI152:
    def test_normalize_returns_image(self, temp_nifti_file):
        """Test that normalization returns a valid image."""
        img = load_bold_image(temp_nifti_file)
        normalized = normalize_to_mni152(img)
        assert isinstance(normalized, nib.Nifti1Image)

    def test_normalize_to_expected_shape(self, temp_nifti_file):
        """Test that normalization produces expected MNI152 shape."""
        img = load_bold_image(temp_nifti_file)
        normalized = normalize_to_mni152(img)
        # Expected shape for 2mm MNI152: (91, 109, 91, n_vols)
        assert normalized.shape[:3] == (91, 109, 91)


class TestSmoothImage:
    def test_smooth_returns_image(self, temp_nifti_file):
        """Test that smoothing returns a valid image."""
        img = load_bold_image(temp_nifti_file)
        smoothed = smooth_image(img, fwhm=6.0)
        assert isinstance(smoothed, nib.Nifti1Image)

    def test_smooth_preserves_shape(self, temp_nifti_file):
        """Test that smoothing preserves image shape."""
        img = load_bold_image(temp_nifti_file)
        smoothed = smooth_image(img, fwhm=6.0)
        assert smoothed.shape == img.shape


class TestBandpassFilter:
    def test_bandpass_returns_image(self, temp_nifti_file):
        """Test that bandpass filtering returns a valid image."""
        img = load_bold_image(temp_nifti_file)
        filtered = bandpass_filter(img, low_freq=0.01, high_freq=0.1, TR=2.0)
        assert isinstance(filtered, nib.Nifti1Image)

    def test_bandpass_preserves_shape(self, temp_nifti_file):
        """Test that bandpass filtering preserves image shape."""
        img = load_bold_image(temp_nifti_file)
        filtered = bandpass_filter(img, low_freq=0.01, high_freq=0.1, TR=2.0)
        assert filtered.shape == img.shape


class TestPreprocessBold:
    def test_preprocess_creates_output_file(self, temp_nifti_file):
        """Test that preprocess_bold creates an output file."""
        with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result = preprocess_bold(temp_nifti_file, output_path)
            assert result.exists()
            assert result == output_path
        finally:
            if output_path.exists():
                os.unlink(output_path)

    def test_preprocess_full_pipeline(self, temp_nifti_file):
        """Test the full preprocessing pipeline."""
        with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result = preprocess_bold(temp_nifti_file, output_path)
            # Load and verify output
            output_img = nib.load(str(result))
            assert output_img.shape[3] == 5  # Same number of volumes
        finally:
            if output_path.exists():
                os.unlink(output_path)


class TestRunPreprocessingPipeline:
    def test_pipeline_processes_multiple_files(self, temp_input_dir):
        """Test that the pipeline processes all files in a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            output_files = run_preprocessing_pipeline(
                input_dir=temp_input_dir,
                output_dir=output_dir
            )
            assert len(output_files) == 2
            for f in output_files:
                assert f.exists()

    def test_pipeline_creates_output_directory(self, temp_input_dir):
        """Test that the pipeline creates the output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "new_subdir"
            assert not output_dir.exists()
            
            output_files = run_preprocessing_pipeline(
                input_dir=temp_input_dir,
                output_dir=output_dir
            )
            assert output_dir.exists()
            assert len(output_files) == 2

    def test_pipeline_with_no_files_raises_error(self):
        """Test that pipeline raises error when no input files are found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            output_dir = Path(tmpdir) / "output"
            
            with pytest.raises(NilearnFallbackError):
                run_preprocessing_pipeline(
                    input_dir=input_dir,
                    output_dir=output_dir
                )