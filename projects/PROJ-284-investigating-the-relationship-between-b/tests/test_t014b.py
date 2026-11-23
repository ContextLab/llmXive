"""Tests for task T014b: tSNR evidence recording and subject filtering."""

import tempfile
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import pytest

from code.data.preprocess import (
    calculate_tsnr,
    record_tsnr_evidence_and_filter,
    _extract_subject_id_from_path,
)

def create_test_nifti(shape: tuple = (10, 10, 10, 100), filename: str = "test.nii.gz") -> Path:
    """Create a test 4D NIfTI file with known tSNR properties."""
    # Create data with high signal in the middle, low at edges
    data = np.random.randn(*shape).astype(np.float32) * 10
    data[3:7, 3:7, 3:7, :] += 50  # High mean signal in center
    img = nib.Nifti1Image(data, np.eye(4))
    path = Path(tempfile.gettempdir()) / filename
    nib.save(img, path)
    return path

def test_calculate_tsnr():
    """Test that calculate_tsnr returns correct shape and values."""
    path = create_test_nifti()
    try:
        img = nib.load(path)
        tsnr = calculate_tsnr(img)
        assert tsnr.shape == (10, 10, 10)
        assert tsnr.dtype in (np.float32, np.float64)
        assert np.all(np.isfinite(tsnr))
        assert np.any(tsnr > 0)  # Some voxels should have positive tSNR
    finally:
        path.unlink()

def test_extract_subject_id_from_path():
    """Test subject ID extraction from file names."""
    assert _extract_subject_id_from_path(Path("123456_rest.nii.gz")) == "123456"
    assert _extract_subject_id_from_path(Path("100307-rest.nii")) == "100307"
    assert _extract_subject_id_from_path(Path("999999.nii.gz")) == "999999"

def test_record_tsnr_evidence_and_filter():
    """Test the full tSNR recording and filtering pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = Path(tmpdir) / "input"
        output_dir = Path(tmpdir) / "output"
        input_dir.mkdir()

        # Create two test NIfTI files
        path1 = input_dir / "100307_rest.nii.gz"
        path2 = input_dir / "100308_rest.nii.gz"

        data1 = np.random.randn(10, 10, 10, 100).astype(np.float32) * 5 + 30
        data2 = np.random.randn(10, 10, 10, 100).astype(np.float32) * 2 + 60

        nib.save(nib.Nifti1Image(data1, np.eye(4)), path1)
        nib.save(nib.Nifti1Image(data2, np.eye(4)), path2)

        # Run the filter
        record_tsnr_evidence_and_filter(
            nifti_dir=input_dir,
            output_dir=output_dir,
            tsnr_threshold=50.0,
            inclusion_percent=90.0,
        )

        # Check that output files were created
        assert (output_dir / "qc_summary.csv").exists()
        assert (output_dir / "subjects_included.csv").exists()

        # Verify QC summary structure
        qc_df = pd.read_csv(output_dir / "qc_summary.csv")
        assert len(qc_df) == 2
        assert "subject_id" in qc_df.columns
        assert "total_voxels" in qc_df.columns
        assert "percent_ge_50" in qc_df.columns

        # Verify included subjects (should be empty or small based on data)
        included_df = pd.read_csv(output_dir / "subjects_included.csv")
        assert "subject_id" in included_df.columns
        assert len(included_df) <= 2

def test_record_tsnr_missing_directory():
    """Test that missing input directory raises error."""
    with pytest.raises(NotADirectoryError):
        record_tsnr_evidence_and_filter(
            nifti_dir=Path("/nonexistent/directory"),
            output_dir=Path("/tmp/output"),
        )

def test_record_tsnr_no_files():
    """Test that empty directory raises error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = Path(tmpdir) / "empty"
        output_dir = Path(tmpdir) / "output"
        input_dir.mkdir()

        with pytest.raises(FileNotFoundError):
            record_tsnr_evidence_and_filter(
                nifti_dir=input_dir,
                output_dir=output_dir,
            )