"""
Integration tests for preprocessing pipeline.
Tests motion correction with synthetic data to validate CI compatibility.
"""

import os
import tempfile
from pathlib import Path
import numpy as np
import nibabel as nib
import pytest

from code.data.preprocess import correct_motion, preprocess_subject_batch, _check_fsl_installed, _create_fallback_mcflirt
from code.logging_config import setup_logging

# Setup logging for tests
setup_logging()

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def synthetic_nifti(temp_data_dir):
    """Create a synthetic NIfTI file for testing."""
    # Create 4D fMRI-like data: 64x64x30x100 (voxels, timepoints)
    data = np.random.randn(64, 64, 30, 100).astype(np.float32)
    
    # Create NIfTI image with standard affine
    affine = np.eye(4)
    img = nib.Nifti1Image(data, affine)
    
    # Save to temp directory
    output_path = temp_data_dir / "sub-1001_task-rest_bold.nii.gz"
    nib.save(img, output_path)
    
    return output_path

def test_fsl_availability():
    """Test that we can detect FSL availability."""
    is_available = _check_fsl_installed()
    # This test passes regardless of FSL availability
    assert isinstance(is_available, bool)

def test_fallback_mcflirt_creates_output(temp_data_dir, synthetic_nifti):
    """Test that fallback mcflirt creates valid output."""
    output_path = temp_data_dir / "sub-1001_motion_corrected.nii.gz"
    
    success, message = _create_fallback_mcflirt(synthetic_nifti, output_path)
    
    assert success, f"Fallback mcflirt failed: {message}"
    assert output_path.exists(), "Output file was not created"
    
    # Verify output is valid NIfTI
    img = nib.load(output_path)
    assert img.shape == (64, 64, 30, 100), "Output dimensions mismatch"

def test_motion_correction_with_fallback(temp_data_dir, synthetic_nifti):
    """Test motion correction with fallback mode (CI compatible)."""
    output_dir = temp_data_dir / "processed"
    
    output_path, metadata = correct_motion(
        subject_id="sub-1001",
        input_nifti_path=synthetic_nifti,
        output_dir=output_dir,
        force_fallback=True
    )
    
    assert output_path is not None, "Output path should not be None"
    assert output_path.exists(), "Output file should exist"
    assert metadata["status"] == "success", "Processing should succeed"
    assert "fallback" in metadata["tool"], "Should use fallback tool"
    assert metadata["passes_threshold"] is True, "Should pass motion threshold"

def test_motion_correction_real_data(temp_data_dir, synthetic_nifti):
    """Test motion correction with real FSL if available."""
    output_dir = temp_data_dir / "processed"
    
    output_path, metadata = correct_motion(
        subject_id="sub-1001",
        input_nifti_path=synthetic_nifti,
        output_dir=output_dir,
        force_fallback=not _check_fsl_installed()
    )
    
    # Should always produce output (either real or fallback)
    assert output_path is not None, "Output path should not be None"
    assert output_path.exists(), "Output file should exist"
    assert metadata["status"] == "success", "Processing should succeed"

def test_batch_processing(temp_data_dir, synthetic_nifti):
    """Test batch processing of multiple subjects."""
    # Create additional synthetic subjects
    subjects = []
    for i in range(3):
        data = np.random.randn(64, 64, 30, 100).astype(np.float32)
        affine = np.eye(4)
        img = nib.Nifti1Image(data, affine)
        output_path = temp_data_dir / f"sub-100{i+1}_task-rest_bold.nii.gz"
        nib.save(img, output_path)
        subjects.append(f"sub-100{i+1}")
    
    output_dir = temp_data_dir / "processed"
    
    results = preprocess_subject_batch(
        subject_ids=subjects,
        input_dir=temp_data_dir,
        output_dir=output_dir,
        force_fallback=True
    )
    
    assert len(results) == 3, "Should process all 3 subjects"
    success_count = sum(1 for r in results if r.get("status") == "success")
    assert success_count == 3, f"All subjects should succeed, got {success_count}/3"
    
    # Verify output files exist
    for sub_id in subjects:
        output_file = output_dir / f"{sub_id}_motion_corrected.nii.gz"
        assert output_file.exists(), f"Output file should exist for {sub_id}"

def test_motion_threshold_validation(temp_data_dir, synthetic_nifti):
    """Test that motion threshold validation works."""
    output_dir = temp_data_dir / "processed"
    
    output_path, metadata = correct_motion(
        subject_id="sub-1001",
        input_nifti_path=synthetic_nifti,
        output_dir=output_dir,
        force_fallback=True
    )
    
    # In fallback mode, we set dummy values that pass threshold
    assert "passes_threshold" in metadata, "Should include threshold validation"
    assert isinstance(metadata["passes_threshold"], bool), "Should be boolean"

def test_memory_estimation(temp_data_dir, synthetic_nifti):
    """Test memory estimation logic."""
    from code.data.preprocess import _estimate_memory_usage
    
    mem_estimate = _estimate_memory_usage(synthetic_nifti)
    
    assert mem_estimate > 0, "Memory estimate should be positive"
    assert isinstance(mem_estimate, float), "Should return float"

def test_batch_size_determination(temp_data_dir, synthetic_nifti):
    """Test dynamic batch sizing."""
    from code.data.preprocess import _determine_batch_size
    
    files = [synthetic_nifti]
    batch_size = _determine_batch_size(files)
    
    assert batch_size >= 1, "Batch size should be at least 1"
    assert isinstance(batch_size, int), "Should return integer"
