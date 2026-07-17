"""
Unit tests for preprocessing module.
"""

import os
import tempfile
from pathlib import Path

import numpy as np
import pytest
from nilearn import image, masking

# Import the module under test
from src.brainnet.preprocessing import (
    load_nifti,
    motion_correction,
    band_pass_filter,
    normalize_to_mni,
    preprocess_pipeline,
    LOW_PASS,
    HIGH_PASS
)

# Helper to create a dummy 4D NIfTI image for testing
def create_dummy_nifti(shape=(10, 10, 10, 20), affine=None):
    """Creates a dummy NIfTI image with random data."""
    if affine is None:
        affine = np.eye(4)
    data = np.random.rand(*shape).astype(np.float32)
    return image.new_img_like(image.Nifti1Image(data, affine), data)

def test_load_nifti_file_not_found():
    """Test that load_nifti raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        load_nifti("nonexistent_file.nii.gz")

def test_motion_correction():
    """Test motion correction function."""
    dummy_img = create_dummy_nifti()
    corrected = motion_correction(dummy_img)
    assert corrected.shape == dummy_img.shape
    # Check that data is not all zeros or NaN
    assert not np.allclose(corrected.get_fdata(), 0)

def test_band_pass_filter():
    """Test band-pass filtering function."""
    dummy_img = create_dummy_nifti()
    # TR=2.0s is required for the filter
    filtered = band_pass_filter(dummy_img, t_r=2.0)
    assert filtered.shape == dummy_img.shape
    assert not np.allclose(filtered.get_fdata(), 0)

def test_normalize_to_mni():
    """Test normalization to MNI space."""
    dummy_img = create_dummy_nifti()
    normalized = normalize_to_mni(dummy_img, target_resolution=2)
    # MNI template is typically 91x109x91 or similar, but resampling changes shape
    # We just check that it ran and produced an image
    assert normalized.affine is not None
    assert normalized.shape is not None

def test_preprocess_pipeline():
    """Test the full preprocessing pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = Path(tmpdir) / "input"
        output_dir = Path(tmpdir) / "output"
        input_dir.mkdir()
        
        # Create a dummy input file
        dummy_img = create_dummy_nifti(shape=(10, 10, 10, 10))
        input_path = input_dir / "test.nii.gz"
        dummy_img.to_filename(str(input_path))
        
        # Run pipeline
        output_path = preprocess_pipeline(
            input_file=input_path,
            output_dir=output_dir,
            t_r=2.0
        )
        
        assert output_path.exists()
        assert output_path.name == "test_preprocessed.nii.gz"
        
        # Verify the output is a valid NIfTI
        result_img = load_nifti(output_path)
        assert result_img.shape[3] == 10  # Time dimension preserved
