"""
Unit tests for spatial normalization functionality.
"""
import os
import tempfile
from pathlib import Path
import numpy as np
import nibabel as nib
import pytest

from preprocessing.normalization import normalize_to_mni, normalize_participant
from utils.io import ensure_dir, file_exists
from utils.logger import get_logger

logger = get_logger(__name__)


def create_dummy_nifti(shape, affine=None, path=None):
    """Helper to create a dummy NIfTI file for testing."""
    if affine is None:
        affine = np.eye(4)
    data = np.random.rand(*shape).astype(np.float32)
    img = nib.Nifti1Image(data, affine)
    if path:
        ensure_dir(path.parent)
        nib.save(img, str(path))
    return img, path


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_normalize_to_mni_creates_file(temp_data_dir):
    """Test that normalize_to_mni creates an output file."""
    # Create a dummy input image
    input_path = temp_data_dir / "input_bold.nii.gz"
    create_dummy_nifti((10, 10, 10, 5), path=input_path)

    output_path = temp_data_dir / "output_norm.nii.gz"

    # Run normalization
    result_path = normalize_to_mni(input_path, output_path)

    # Assertions
    assert result_path.exists(), f"Output file {result_path} was not created"
    assert result_path == output_path

    # Verify the output is a valid NIfTI
    loaded_img = nib.load(str(result_path))
    assert loaded_img.shape[0] > 0  # Should have been resampled to template shape (approx)


def test_normalize_to_mni_nonexistent_input(temp_data_dir):
    """Test that normalize_to_mni raises error for missing input."""
    input_path = temp_data_dir / "nonexistent.nii.gz"
    output_path = temp_data_dir / "out.nii.gz"

    with pytest.raises(Exception): # IOLoadError or FileNotFoundError
        normalize_to_mni(input_path, output_path)


def test_normalize_participant_integration(temp_data_dir):
    """
    Integration test for normalize_participant.
    Mocks the directory structure and verifies normalization of multiple runs.
    """
    # Setup directory structure
    # data_root/processed/sub-01/sub-01_task-social_bold_preproc.nii.gz
    data_root = temp_data_dir / "data"
    processed_root = temp_data_dir / "processed"
    sub_dir = data_root / "processed" / "sub-01"
    ensure_dir(sub_dir)

    # Create dummy preprocessed files
    run1 = sub_dir / "sub-01_task-social_bold_preproc.nii.gz"
    run2 = sub_dir / "sub-01_task-rest_bold_preproc.nii.gz"
    create_dummy_nifti((10, 10, 10, 5), path=run1)
    create_dummy_nifti((10, 10, 10, 5), path=run2)

    # Run normalization
    results = normalize_participant(
        participant_id="sub-01",
        data_root=data_root,
        processed_root=processed_root,
    )

    # Check results
    assert len(results) == 2, f"Expected 2 files, got {len(results)}"

    # Verify output files exist
    for key, path in results.items():
        assert path.exists(), f"Normalized file {path} does not exist"
        assert "norm" in path.name, f"Output filename should contain 'norm': {path.name}"
        # Verify it's a valid NIfTI
        try:
            nib.load(str(path))
        except Exception as e:
            pytest.fail(f"Output file {path} is not a valid NIfTI: {e}")
