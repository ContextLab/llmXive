"""
Unit tests for ``code.utils.loaders.load_chunked_fMRI``.
The tests create a tiny synthetic NIfTI image on‑disk, stream it using the
loader and verify that the concatenated output matches the original data.
"""
import json
import os
import tempfile
from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

# Import the function under test
from utils.loaders import load_chunked_fMRI


@pytest.fixture
def tiny_nifti(tmp_path: Path) -> Path:
    """
    Create a small (2×2×2 voxels, 5 timepoints) NIfTI image with known data.
    """
    shape = (2, 2, 2, 5)
    rng = np.random.default_rng(0)
    data = rng.random(shape, dtype=np.float32)

    affine = np.eye(4)
    img = nib.Nifti1Image(data, affine)

    fp = tmp_path / "tiny.nii.gz"
    img.to_filename(str(fp))
    return fp


def test_load_chunked_fMRI_basic(tiny_nifti: Path):
    """
    Load the synthetic image in chunks and ensure the reconstructed array
    matches the original.
    """
    # Load the original data for comparison
    original_img = nib.load(str(tiny_nifti))
    original_data = original_img.get_fdata(dtype=np.float32)

    # Stream with a deliberately small chunk size to exercise the loop
    streamed_chunks = list(load_chunked_fMRI(tiny_nifti, chunk_size=2))

    # Re‑assemble the chunks along the time axis
    reconstructed = np.concatenate(streamed_chunks, axis=3)

    assert reconstructed.shape == original_data.shape
    # Use ``np.allclose`` because floating‑point rounding may differ slightly
    assert np.allclose(reconstructed, original_data, atol=1e-6)


def test_load_chunked_fMRI_invalid_path():
    """
    The loader must raise ``FileNotFoundError`` for a non‑existent file.
    """
    with pytest.raises(FileNotFoundError):
        list(load_chunked_fMRI("non_existent_file.nii.gz"))