"""
Unit tests for the mock NIfTI generation functionality.

These tests verify that the generated mock NIfTI file meets the
requirements specified in task T017c:
- Correct dimensions
- Correct data type (float32)
- Valid header (pixdim and sform)
- File exists at the expected path
"""

import os
import pytest
import nibabel as nib
import numpy as np
from pathlib import Path

# Import the generation function
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))
from generate_mock_nifti import generate_mock_nifti, OUTPUT_FILE, OUTPUT_DIR, DIMENSIONS, PIXDIM

class TestMockNiftiGeneration:
    """Test cases for mock NIfTI file generation."""
    
    def test_file_exists(self):
        """Test that the mock NIfTI file exists at the expected path."""
        # Ensure the file is generated
        from generate_mock_nifti import main
        main()
        
        assert OUTPUT_FILE.exists(), f"Mock NIfTI file not found at {OUTPUT_FILE}"
    
    def test_data_shape(self):
        """Test that the generated data has the correct shape."""
        from generate_mock_nifti import main
        main()
        
        img = nib.load(str(OUTPUT_FILE))
        data = img.get_fdata()
        
        assert data.shape == DIMENSIONS, f"Expected shape {DIMENSIONS}, got {data.shape}"
    
    def test_data_dtype(self):
        """Test that the data type is float32."""
        from generate_mock_nifti import main
        main()
        
        img = nib.load(str(OUTPUT_FILE))
        data = img.get_fdata()
        
        assert data.dtype == np.float32, f"Expected float32, got {data.dtype}"
    
    def test_pixdim(self):
        """Test that the header has valid pixdim values."""
        from generate_mock_nifti import main
        main()
        
        img = nib.load(str(OUTPUT_FILE))
        header = img.header
        zooms = header.get_zooms()
        
        # Check spatial dimensions (first 3)
        assert zooms[0] == PIXDIM[0], f"Expected x-dim {PIXDIM[0]}, got {zooms[0]}"
        assert zooms[1] == PIXDIM[1], f"Expected y-dim {PIXDIM[1]}, got {zooms[1]}"
        assert zooms[2] == PIXDIM[2], f"Expected z-dim {PIXDIM[2]}, got {zooms[2]}"
    
    def test_sform_valid(self):
        """Test that the sform matrix is valid (invertible and reasonable)."""
        from generate_mock_nifti import main
        main()
        
        img = nib.load(str(OUTPUT_FILE))
        sform = img.affine
        
        # Check that sform is not identity (has offsets)
        assert not np.allclose(sform, np.eye(4)), "Sform should not be identity matrix"
        
        # Check that sform is invertible
        det = np.linalg.det(sform[:3, :3])
        assert not np.isclose(det, 0), "Sform should be invertible"
        
        # Check that sform has reasonable scale (voxel dimensions)
        scales = np.sqrt(np.sum(sform[:3, :3]**2, axis=0))
        assert all(1.0 <= s <= 10.0 for s in scales), f"Scales should be reasonable: {scales}"
    
    def test_data_is_zeros(self):
        """Test that the data array contains only zeros (as specified)."""
        from generate_mock_nifti import main
        main()
        
        img = nib.load(str(OUTPUT_FILE))
        data = img.get_fdata()
        
        assert np.allclose(data, 0), "Mock data should be all zeros"
    
    def test_4d_structure(self):
        """Test that the data has 4 dimensions (x, y, z, time)."""
        from generate_mock_nifti import main
        main()
        
        img = nib.load(str(OUTPUT_FILE))
        data = img.get_fdata()
        
        assert len(data.shape) == 4, f"Expected 4D data, got {len(data.shape)}D"
        assert data.shape[3] == 50, f"Expected 50 timepoints, got {data.shape[3]}"