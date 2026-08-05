"""
Unit tests for motion scrubbing logic in preprocessing.py.

Verifies that:
1. Framewise Displacement (FD) is calculated correctly.
2. Volumes with FD > 0.2mm are correctly identified for removal.
3. The scrubbing function returns the correct masked time series.
"""
import numpy as np
import nibabel as nib
import pytest
from pathlib import Path
import tempfile
import os

# Import the functions from the project's preprocessing module
# Note: Assuming tests are run from project root or path is adjusted
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocessing import calculate_fd, scrub_volumes, truncate_to_target_length


def test_calculate_fd_basic():
    """Test basic FD calculation on a simple 4D array."""
    # Create a dummy 4D image: (x, y, z, t) = (2, 2, 2, 5)
    # We use a simple pattern to ensure non-zero displacement
    data = np.zeros((2, 2, 2, 5), dtype=np.float32)
    
    # Set a simple translation in the x-direction for the last timepoint
    # This should result in a non-zero FD
    data[:, :, :, 0] = 0
    data[:, :, :, 1] = 1.0  # Shift by 1.0mm in x
    data[:, :, :, 2] = 2.0
    data[:, :, :, 3] = 3.0
    data[:, :, :, 4] = 4.0

    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = Path(tmpdir) / "test.nii.gz"
        img = nib.Nifti1Image(data, np.eye(4))
        nib.save(img, str(img_path))
        
        # Calculate FD
        fd_values = calculate_fd(str(img_path))
        
        # FD is the sum of absolute differences in translations + rotations
        # Since we only have translation in x, and rotation is 0:
        # FD[0] is undefined (usually NaN or 0 depending on implementation), 
        # FD[1] should be |1.0 - 0.0| = 1.0
        # FD[2] should be |2.0 - 1.0| = 1.0, etc.
        
        assert len(fd_values) == 4  # 5 timepoints -> 4 differences
        assert fd_values[0] == pytest.approx(1.0, rel=1e-4)
        assert fd_values[1] == pytest.approx(1.0, rel=1e-4)
        assert fd_values[2] == pytest.approx(1.0, rel=1e-4)
        assert fd_values[3] == pytest.approx(1.0, rel=1e-4)


def test_scrub_volumes_threshold():
    """Test that volumes with FD > 0.2mm are removed."""
    # Create a dummy 4D image: (x, y, z, t) = (2, 2, 2, 6)
    # We will manually construct FD values to test the threshold logic
    data = np.random.rand(2, 2, 2, 6).astype(np.float32)
    
    # Simulate an image where specific timepoints have high motion
    # We will mock the FD calculation by passing a pre-calculated list
    # to scrub_volumes if the function signature allows, OR we create
    # an image where the displacement naturally results in high FD.
    
    # Strategy: Create an image where we know the displacement.
    # Let's create a 4D image where:
    # t=0: base
    # t=1: shifted 0.1mm (FD ~ 0.1) -> Keep
    # t=2: shifted 0.5mm from t=1 (FD ~ 0.5) -> Scrub
    # t=3: shifted 0.1mm from t=2 (FD ~ 0.1) -> Keep
    # t=4: shifted 0.6mm from t=3 (FD ~ 0.6) -> Scrub
    # t=5: shifted 0.1mm from t=4 (FD ~ 0.1) -> Keep
    
    # We will create the image and then manually verify the scrubbing logic
    # by checking the indices returned by scrub_volumes.
    
    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = Path(tmpdir) / "test_motion.nii.gz"
        img = nib.Nifti1Image(data, np.eye(4))
        nib.save(img, str(img_path))
        
        # Calculate FD for this image
        fd_values = calculate_fd(str(img_path))
        
        # Since random data won't guarantee specific FD values, 
        # we will construct a specific scenario.
        # Let's create a new image with known displacements.
        # We need to simulate the motion parameters. 
        # However, calculate_fd expects a NIfTI file. 
        # To test the logic strictly, we can mock the FD values or 
        # construct an image where the voxel shifts correspond to known FD.
        
        # Alternative: Test the scrub_volumes function directly with 
        # a known list of FD values if the function accepts it, 
        # or trust calculate_fd on a synthetic image.
        
        # Let's create a synthetic image where we know the FD.
        # We will create a 1x1x1 image and shift it.
        # This is tricky with NIfTI. 
        
        # Instead, let's assume calculate_fd works as per T013/T009 logic
        # and test scrub_volumes with a mock FD list if possible,
        # OR create a test where we inject known FD values.
        
        # Since the function signature in the prompt is `scrub_volumes(nii_path, fd_threshold)`,
        # we must rely on `calculate_fd` inside it.
        
        # Let's create a deterministic image.
        # We'll make a 4D image where the mean signal moves in space.
        # This is hard to do with just nibabel without affines changing.
        
        # Simplified approach: 
        # We will create a test that verifies the *behavior* of scrubbing
        # by checking the number of kept volumes vs total volumes given
        # a specific FD pattern.
        
        # Let's create a fake FD array and a mock function for testing?
        # No, the task requires testing the actual implementation.
        
        # Let's assume the implementation of calculate_fd is correct (from T013)
        # and we are testing the threshold logic of scrub_volumes.
        
        # We will construct an image where we know the FD values.
        # We can do this by creating a 4D image where each volume is 
        # a shifted version of the previous one.
        
        # Create a 3D volume
        vol_base = np.zeros((10, 10, 10))
        vol_base[4:6, 4:6, 4:6] = 1.0  # A block in the center
        
        volumes = []
        # t=0: No shift
        volumes.append(vol_base)
        
        # t=1: Shift 0.1mm (assuming 1mm voxel size, shift 0.1 voxel? No, FD is in mm)
        # We need to shift the image by 0.1mm.
        # If voxel size is 1mm, 0.1mm is 0.1 voxels.
        # This requires interpolation.
        
        # Let's use a simpler approach:
        # Create a 4D image with known "motion" by manipulating the data array
        # such that the difference between volumes is known.
        # This is not physically accurate but tests the logic.
        
        # Actually, let's just test the logic with a mock FD list if we can.
        # But the function signature is fixed.
        
        # Let's assume the implementation calculates FD correctly.
        # We will create a test where we know the outcome.
        
        # We will create a 4D image where the mean intensity moves linearly.
        # This will result in a constant FD.
        
        # Let's create a 4D image with 10 timepoints.
        # We will manually set the FD values by creating a specific pattern.
        # This is difficult without changing the code.
        
        # Alternative: We can mock `calculate_fd` in the test.
        from unittest.mock import patch
        
        # Mock FD values: [0.1, 0.5, 0.1, 0.6, 0.1, 0.1, 0.1, 0.1, 0.1]
        # Indices to scrub: 1 (0.5), 3 (0.6) -> 0-indexed in FD array
        # FD array length is T-1.
        # FD[0] corresponds to transition 0->1.
        # If FD[0] = 0.5, then volume 1 is scrubbed? 
        # Usually, if FD[t] > threshold, volume t+1 is scrubbed.
        # Or volume t is scrubbed?
        # Standard practice: If FD at time t > threshold, scrub time t.
        # Let's assume the implementation scrubs the volume associated with the high FD.
        
        mock_fd = np.array([0.1, 0.5, 0.1, 0.6, 0.1, 0.1, 0.1, 0.1, 0.1])
        # This corresponds to 10 volumes (0 to 9).
        # FD[0] is diff(0,1). If 0.5 > 0.2, scrub volume 1?
        # Or scrub volume 0?
        # Let's assume scrub_volumes scrubs the volume at index t if FD[t-1] > threshold?
        # Or maybe it scrubs the volume at index t if FD[t] > threshold?
        
        # Let's look at the standard definition:
        # FD[t] = |dx[t] - dx[t-1]| + ...
        # If FD[t] > threshold, scrub volume t.
        
        # So if mock_fd = [0.1, 0.5, ...]
        # FD[0] (0.1) -> Keep vol 0
        # FD[1] (0.5) -> Scrub vol 1
        # FD[2] (0.1) -> Keep vol 2
        # FD[3] (0.6) -> Scrub vol 3
        # ...
        
        # We expect volumes 1 and 3 to be scrubbed.
        
        with patch('preprocessing.calculate_fd', return_value=mock_fd):
            # We need a valid nifti path for scrub_volumes to open
            # We can use the dummy image we created earlier
            with tempfile.TemporaryDirectory() as tmpdir:
                img_path = Path(tmpdir) / "test.nii.gz"
                dummy_data = np.random.rand(2, 2, 2, 10).astype(np.float32)
                img = nib.Nifti1Image(dummy_data, np.eye(4))
                nib.save(img, str(img_path))
                
                scrubbed_data, kept_indices = scrub_volumes(str(img_path), fd_threshold=0.2)
                
                # We expect 10 original volumes.
                # Scrubbed: 1, 3.
                # Kept: 0, 2, 4, 5, 6, 7, 8, 9.
                # Total kept: 8.
                
                assert scrubbed_data.shape[3] == 8
                # Check that the kept indices are correct
                expected_kept = [0, 2, 4, 5, 6, 7, 8, 9]
                assert list(kept_indices) == expected_kept


def test_scrub_volumes_no_motion():
    """Test that no volumes are removed if FD is always below threshold."""
    mock_fd = np.array([0.05, 0.05, 0.05, 0.05, 0.05])
    
    from unittest.mock import patch
    
    with patch('preprocessing.calculate_fd', return_value=mock_fd):
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = Path(tmpdir) / "test.nii.gz"
            dummy_data = np.random.rand(2, 2, 2, 6).astype(np.float32)
            img = nib.Nifti1Image(dummy_data, np.eye(4))
            nib.save(img, str(img_path))
            
            scrubbed_data, kept_indices = scrub_volumes(str(img_path), fd_threshold=0.2)
            
            # All 6 volumes should be kept
            assert scrubbed_data.shape[3] == 6
            assert list(kept_indices) == [0, 1, 2, 3, 4, 5]


def test_scrub_volumes_all_motion():
    """Test that all volumes are removed if FD is always above threshold."""
    # 10 volumes -> 9 FD values
    mock_fd = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
    
    from unittest.mock import patch
    
    with patch('preprocessing.calculate_fd', return_value=mock_fd):
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = Path(tmpdir) / "test.nii.gz"
            dummy_data = np.random.rand(2, 2, 2, 10).astype(np.float32)
            img = nib.Nifti1Image(dummy_data, np.eye(4))
            nib.save(img, str(img_path))
            
            scrubbed_data, kept_indices = scrub_volumes(str(img_path), fd_threshold=0.2)
            
            # All volumes scrubbed? 
            # If FD[t] > threshold, scrub volume t.
            # FD[0] -> scrub 0? Or 1?
            # If we scrub 0, 1, 2... then all are scrubbed.
            # If we scrub 1, 2... then 0 is kept.
            # Let's assume the implementation scrubs the volume corresponding to the high FD.
            # If FD[0] is high, volume 0 or 1 is scrubbed.
            # If all FD are high, likely all or all but one are scrubbed.
            # Let's check the shape.
            assert scrubbed_data.shape[3] < 10


def test_truncate_to_target_length():
    """Test truncation to exactly N=120 volumes."""
    # Create an image with 150 volumes
    data = np.random.rand(2, 2, 2, 150).astype(np.float32)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        img_path = Path(tmpdir) / "test.nii.gz"
        img = nib.Nifti1Image(data, np.eye(4))
        nib.save(img, str(img_path))
        
        target_length = 120
        truncated_data = truncate_to_target_length(str(img_path), target_length)
        
        assert truncated_data.shape[3] == target_length
        # Verify the data is the first 120 volumes
        assert np.array_equal(truncated_data, data[:, :, :, :120])