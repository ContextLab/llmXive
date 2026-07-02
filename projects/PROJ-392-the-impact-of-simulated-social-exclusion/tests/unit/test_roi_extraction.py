"""
Unit tests for the ROI Extraction module.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import numpy as np
import nibabel as nib
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from analysis.roi_extraction import (
    get_aal_vs_mask,
    get_ho_ofo_mask,
    create_coordinate_mask,
    extract_beta_from_glm_results
)


class TestROIMaskGeneration(unittest.TestCase):
    
    def test_create_coordinate_mask(self):
        """Test creation of a spherical mask from MNI coordinates."""
        mask = create_coordinate_mask(mni_coords=[(0, 0, 0)], radius=5)
        self.assertIsInstance(mask, nib.Nifti1Image)
        
        data = mask.get_fdata()
        # Check that there are some non-zero voxels
        self.assertGreater(np.sum(data), 0)
        
        # Check shape and affine
        self.assertEqual(len(data.shape), 3)
        self.assertIsNotNone(mask.affine)

    @patch('analysis.roi_extraction.fetch_atlas_aal')
    def test_get_aal_vs_mask_fallback(self, mock_fetch):
        """Test AAL mask generation with fallback to coordinate mask."""
        # Mock AAL to return no specific VS labels
        mock_fetch.return_value = MagicMock()
        mock_fetch.return_value.maps = nib.Nifti1Image(np.zeros((10, 10, 10)), np.eye(4))
        mock_fetch.return_value.labels = ["OtherLabel", "AnotherLabel"]
        
        # This should trigger the coordinate-based fallback
        with patch('analysis.roi_extraction.create_coordinate_mask') as mock_coord:
            mock_coord.return_value = nib.Nifti1Image(np.ones((10, 10, 10)), np.eye(4))
            mask = get_aal_vs_mask()
            
            # Verify create_coordinate_mask was called
            mock_coord.assert_called_once()
            self.assertIsInstance(mask, nib.Nifti1Image)


class TestBetaExtraction(unittest.TestCase):
    
    @patch('nibabel.load')
    def test_extract_beta_from_glm_results(self, mock_load):
        """Test extraction of beta values from a mock GLM result."""
        # Create mock image data
        data = np.random.rand(10, 10, 10)
        mock_img = MagicMock()
        mock_img.get_fdata.return_value = data
        mock_img.affine = np.eye(4)
        mock_load.return_value = mock_img
        
        # Create a simple ROI mask (all 1s for simplicity in this test)
        roi_data = np.ones((10, 10, 10))
        roi_img = nib.Nifti1Image(roi_data, np.eye(4))
        
        # Mock the file existence check
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.glob', return_value=[MagicMock()]):
                beta = extract_beta_from_glm_results(
                    subject_id="sub-01",
                    dataset_id="ds000246",
                    roi_img=roi_img,
                    glm_results_dir=Path("/fake/path"),
                    contrast_name="reward"
                )
                
                # Beta should be the mean of the random data
                self.assertAlmostEqual(beta, np.mean(data), places=5)


if __name__ == "__main__":
    unittest.main()