"""
Unit tests for create_auditory_roi.py
"""
import os
import tempfile
from pathlib import Path
import numpy as np
import nibabel as nib
from unittest.mock import patch, MagicMock

# Import the functions to test
from create_auditory_roi import fetch_harvard_oxford_atlas, create_auditory_cortex_mask

def test_fetch_harvard_oxford_atlas_structure():
    """
    Test that the fetch function returns expected structure.
    Note: We mock the actual download to avoid network calls in tests.
    """
    # Create mock data
    mock_data = np.random.randint(0, 10, (10, 10, 10))
    mock_img = nib.Nifti1Image(mock_data, np.eye(4))
    mock_labels = ["", "Frontal Pole", "Insular Cortex", "Auditory Cortex", "Visual Cortex"]

    with patch('create_auditory_roi.datasets.fetch_atlas_harvard_oxford') as mock_fetch:
        mock_fetch.return_value = {
            'maps': mock_img,
            'labels': mock_labels
        }

        img, labels = fetch_harvard_oxford_atlas()

        assert isinstance(img, nib.Nifti1Image)
        assert len(labels) == len(mock_labels)
        assert "Auditory Cortex" in labels
        mock_fetch.assert_called_once()

def test_create_auditory_cortex_mask_extraction():
    """
    Test that the mask is correctly extracted for a known label.
    """
    # Create a simple synthetic atlas where index 3 is Auditory Cortex
    # Shape: (5, 5, 5)
    atlas_data = np.zeros((5, 5, 5), dtype=np.int16)
    atlas_data[1:3, 1:3, 1:3] = 3  # Region of interest
    atlas_data[4, 4, 4] = 2       # Another region

    mock_img = nib.Nifti1Image(atlas_data, np.eye(4))
    mock_labels = ["", "Region A", "Region B", "Auditory Cortex", "Region D"]

    mask_img = create_auditory_cortex_mask(mock_img, mock_labels, "Auditory Cortex")

    mask_data = mask_img.get_fdata()

    # Check that the mask is binary
    assert np.all(np.isin(mask_data, [0, 1]))

    # Check that the correct region is masked
    expected_mask = np.zeros((5, 5, 5), dtype=np.int16)
    expected_mask[1:3, 1:3, 1:3] = 1

    assert np.array_equal(mask_data, expected_mask)

def test_create_auditory_cortex_mask_missing_label():
    """
    Test that a ValueError is raised if the label is not found.
    """
    atlas_data = np.zeros((5, 5, 5), dtype=np.int16)
    mock_img = nib.Nifti1Image(atlas_data, np.eye(4))
    mock_labels = ["", "Region A", "Region B"]

    try:
        create_auditory_cortex_mask(mock_img, mock_labels, "NonExistentRegion")
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "NonExistentRegion" in str(e)

def test_mask_affine_preservation():
    """
    Test that the mask preserves the affine matrix of the input atlas.
    """
    custom_affine = np.array([
        [2.0, 0.0, 0.0, -90.0],
        [0.0, 2.0, 0.0, -126.0],
        [0.0, 0.0, 2.0, -72.0],
        [0.0, 0.0, 0.0, 1.0]
    ])

    atlas_data = np.zeros((10, 10, 10), dtype=np.int16)
    atlas_data[5, 5, 5] = 3
    mock_img = nib.Nifti1Image(atlas_data, custom_affine)
    mock_labels = ["", "A", "B", "Auditory Cortex"]

    mask_img = create_auditory_cortex_mask(mock_img, mock_labels)

    assert np.allclose(mask_img.affine, custom_affine)