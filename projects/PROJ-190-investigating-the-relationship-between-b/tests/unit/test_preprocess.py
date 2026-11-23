"""
Unit tests for preprocessing quality metrics (Framewise Displacement calculation).

This test suite verifies the correctness of the FD calculation logic in
code/data/preprocess.py. It uses synthetic motion parameter data to ensure
the mathematical implementation matches the standard Power et al. (2012) formula:
FD = |Δdx| + |Δdy| + |Δdz| + |Δα| + |Δβ| + |Δγ|

Note: We test the *calculation logic* here. We do not generate synthetic fMRI
volumes (which would be fabrication). We mock the input motion parameters
directly to verify the math.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path to allow imports from code/
# Assuming tests/unit is at depth 2 from root, and code is at depth 1
# We need to import from code.data.preprocess
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.preprocess import calculate_framewise_displacement


class TestFramewiseDisplacementCalculation:
    """Tests for the calculate_framewise_displacement function."""

    def test_zero_motion(self):
        """FD should be zero if there is no motion between volumes."""
        # 6 motion parameters: [x, y, z, roll, pitch, yaw]
        # All zeros means no motion
        motion_params = np.zeros((10, 6))
        
        fd = calculate_framewise_displacement(motion_params)
        
        # FD should be an array of zeros (length N-1)
        assert fd.shape == (9,)
        assert np.allclose(fd, 0.0)

    def test_simple_translation(self):
        """Test FD calculation with pure translation (x-axis)."""
        # Create motion parameters with step change in x only
        # Volume 0: x=0
        # Volume 1: x=0.5 (shift of 0.5 mm)
        # Volume 2: x=0.5 (no shift)
        motion_params = np.zeros((3, 6))
        motion_params[1, 0] = 0.5  # 0.5mm shift in x at volume 1
        
        fd = calculate_framewise_displacement(motion_params)
        
        # FD[0] should be |0.5 - 0| = 0.5
        # FD[1] should be |0.5 - 0.5| = 0.0
        assert np.isclose(fd[0], 0.5)
        assert np.isclose(fd[1], 0.0)

    def test_rotation_conversion(self):
        """Test that rotation parameters are converted to mm displacement."""
        # Power et al. formula uses rotation in radians converted to mm
        # Displacement = radius * angle (in radians)
        # Standard radius used is 50mm
        # If we have 1 radian rotation, displacement should be 50mm
        
        # Create motion params: 0 rotation at vol 0, 1 radian at vol 1
        motion_params = np.zeros((2, 6))
        motion_params[1, 3] = 1.0  # 1 radian rotation (roll)
        
        fd = calculate_framewise_displacement(motion_params)
        
        # Expected FD = |0| + |0| + |0| + |50 * 1.0| + |0| + |0| = 50.0
        # Note: The implementation should handle the 50mm radius conversion internally
        expected_fd = 50.0
        assert np.isclose(fd[0], expected_fd, atol=1e-6)

    def test_combined_motion(self):
        """Test FD with combined translation and rotation."""
        # Vol 0: all zeros
        # Vol 1: x=1.0, y=1.0, roll=0.01 radians
        motion_params = np.zeros((2, 6))
        motion_params[1, 0] = 1.0  # 1mm x
        motion_params[1, 1] = 1.0  # 1mm y
        motion_params[1, 3] = 0.01 # 0.01 rad roll -> 0.5mm displacement
        
        fd = calculate_framewise_displacement(motion_params)
        
        # Expected: |1| + |1| + |0| + |50*0.01| + |0| + |0| = 1 + 1 + 0.5 = 2.5
        expected_fd = 2.5
        assert np.isclose(fd[0], expected_fd, atol=1e-6)

    def test_mean_fd_calculation(self):
        """Test that mean FD is calculated correctly."""
        # Create a sequence with known FDs
        # Vol 0: 0
        # Vol 1: 0.2mm shift -> FD=0.2
        # Vol 2: 0.3mm shift -> FD=0.3
        # Vol 3: 0.1mm shift -> FD=0.1
        motion_params = np.zeros((4, 6))
        motion_params[1, 0] = 0.2
        motion_params[2, 0] = 0.5  # 0.2 + 0.3 = 0.5 total
        motion_params[3, 0] = 0.6  # 0.5 + 0.1 = 0.6 total
        
        fd = calculate_framewise_displacement(motion_params)
        mean_fd = np.mean(fd)
        
        # FDs: [0.2, 0.3, 0.1]
        # Mean: (0.2 + 0.3 + 0.1) / 3 = 0.2
        assert np.isclose(mean_fd, 0.2)

    def test_high_motion_detection(self):
        """Test detection of high motion subjects (FD > 0.5)."""
        # Create a subject with mean FD > 0.5
        motion_params = np.zeros((10, 6))
        # Large jumps in motion
        for i in range(1, 10):
            motion_params[i, 0] = i * 0.2  # Increasing x displacement
        
        fd = calculate_framewise_displacement(motion_params)
        mean_fd = np.mean(fd)
        
        # Verify mean FD is > 0.5
        assert mean_fd > 0.5

    def test_edge_case_single_volume(self):
        """Test behavior with single volume (should return empty array)."""
        motion_params = np.zeros((1, 6))
        
        fd = calculate_framewise_displacement(motion_params)
        
        # Should return empty array
        assert len(fd) == 0

    def test_dtype_preservation(self):
        """Test that output dtype is float."""
        motion_params = np.zeros((5, 6), dtype=np.float32)
        
        fd = calculate_framewise_displacement(motion_params)
        
        assert fd.dtype in [np.float32, np.float64]

    def test_negative_motion(self):
        """Test that negative motion values are handled correctly (absolute value)."""
        # Vol 0: x=0
        # Vol 1: x=-0.5
        motion_params = np.zeros((2, 6))
        motion_params[1, 0] = -0.5
        
        fd = calculate_framewise_displacement(motion_params)
        
        # FD should be | -0.5 | = 0.5 (absolute value)
        assert np.isclose(fd[0], 0.5)

    def test_quality_threshold_compliance(self):
        """Test that mean FD calculation aligns with quality thresholds."""
        # Test case: Subject with mean FD exactly at threshold (0.2)
        motion_params = np.zeros((6, 6))
        # Create 5 volumes with 0.2mm displacement each
        for i in range(1, 6):
            motion_params[i, 0] = i * 0.2
        
        fd = calculate_framewise_displacement(motion_params)
        mean_fd = np.mean(fd)
        
        # This should be exactly 0.2 (or very close due to floating point)
        # (0.2 + 0.2 + 0.2 + 0.2 + 0.2) / 5 = 0.2
        assert np.isclose(mean_fd, 0.2, atol=1e-6)

        # Test case: Subject just above threshold (0.2001)
        motion_params_high = np.zeros((6, 6))
        for i in range(1, 6):
            motion_params_high[i, 0] = i * 0.2001
        
        fd_high = calculate_framewise_displacement(motion_params_high)
        mean_fd_high = np.mean(fd_high)
        
        assert mean_fd_high > 0.2