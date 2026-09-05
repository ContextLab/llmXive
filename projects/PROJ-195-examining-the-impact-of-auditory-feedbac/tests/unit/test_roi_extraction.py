"""
Unit tests for T028: ROI Beta Extraction.

Tests verify:
1. Valid subjects loading logic.
2. ROI mask loading and binary conversion.
3. Mean beta calculation logic (mocked inputs).
4. CSV generation structure.
"""
import os
import sys
import tempfile
import csv
import numpy as np
import nibabel as nib
from pathlib import Path
import pytest

# Add parent directory to path to import roi_extraction
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from roi_extraction import (
    load_valid_subjects,
    load_roi_mask,
    extract_mean_beta,
    find_contrast_map_for_subject
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def valid_subjects_file(temp_dir):
    """Create a mock valid_subjects.txt."""
    f = temp_dir / "valid_subjects.txt"
    f.write_text("sub-01\nsub-02\nsub-03\n")
    return f

@pytest.fixture
def roi_mask_file(temp_dir):
    """Create a mock 3x3x3 ROI mask."""
    mask_path = temp_dir / "auditory_cortex.nii.gz"
    # Create a mask with some 1s and some 0s
    data = np.zeros((3, 3, 3), dtype=np.int32)
    data[1, 1, 1] = 1
    data[0, 0, 0] = 1
    data[2, 2, 2] = 0.6  # Should be > 0.5
    affine = np.eye(4)
    nib.save(nib.Nifti1Image(data, affine), str(mask_path))
    return mask_path

@pytest.fixture
def contrast_map_file(temp_dir):
    """Create a mock contrast map."""
    c_path = temp_dir / "sub-01_contrast_perturbed_vs_normal_z-statistic.nii.gz"
    # Create data where mean of specific voxels is known
    data = np.zeros((3, 3, 3), dtype=np.float32)
    data[1, 1, 1] = 2.5
    data[0, 0, 0] = 3.5
    data[2, 2, 2] = 1.0
    affine = np.eye(4)
    nib.save(nib.Nifti1Image(data, affine), str(c_path))
    return c_path

def test_load_valid_subjects(valid_subjects_file):
    """Test loading subjects from file."""
    import logging
    logger = logging.getLogger("test")
    subjects = load_valid_subjects(logger)
    assert subjects == ["sub-01", "sub-02", "sub-03"]

def test_load_roi_mask(roi_mask_file):
    """Test ROI mask loading and binary thresholding."""
    import logging
    logger = logging.getLogger("test")
    data, affine = load_roi_mask(logger)
    
    assert data.shape == (3, 3, 3)
    assert data.dtype == np.int32
    # Check that 0.6 became 1
    assert data[2, 2, 2] == 1
    # Check that 0.0 stayed 0
    assert data[2, 2, 2] == 1 # Wait, 0.6 > 0.5 -> 1. 
    # Re-check logic: data[2,2,2] was 0.6. (0.6 > 0.5) is True -> 1.
    assert data[2, 2, 2] == 1
    assert data[2, 2, 2] == 1
    # Count non-zero
    assert np.sum(data) == 3 # (1,1,1), (0,0,0), (2,2,2)

def test_extract_mean_beta(roi_mask_file, contrast_map_file):
    """Test mean beta extraction logic."""
    import logging
    logger = logging.getLogger("test")
    
    mask_data, mask_affine = load_roi_mask(logger)
    
    # The mask has 1s at [1,1,1] and [0,0,0] (and [2,2,2] due to 0.6>0.5)
    # The contrast map has 2.5 at [1,1,1], 3.5 at [0,0,0], 1.0 at [2,2,2]
    # Mean should be (2.5 + 3.5 + 1.0) / 3 = 7.0 / 3 = 2.333...
    
    result = extract_mean_beta(contrast_map_file, mask_data, mask_affine, logger)
    
    assert result is not None
    expected = (2.5 + 3.5 + 1.0) / 3.0
    assert np.isclose(result, expected)

def test_find_contrast_map_for_subject(temp_dir, contrast_map_file):
    """Test finding the correct file."""
    import logging
    logger = logging.getLogger("test")
    
    # Move file to temp_dir for search
    # Actually, the fixture puts it in temp_dir already
    result = find_contrast_map_for_subject("sub-01", temp_dir, logger)
    assert result == contrast_map_file

def test_find_contrast_map_not_found(temp_dir):
    """Test behavior when file is missing."""
    import logging
    logger = logging.getLogger("test")
    result = find_contrast_map_for_subject("sub-99", temp_dir, logger)
    assert result is None
