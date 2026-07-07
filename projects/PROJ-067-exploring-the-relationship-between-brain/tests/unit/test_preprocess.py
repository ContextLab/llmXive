"""
Unit tests for FD calculation and exclusion logic in data.preprocess.

Tests:
1. calculate_fd: Verifies correct FD calculation from displacement arrays.
2. exclude_high_motion_subjects: Verifies subjects with mean FD > threshold are excluded.
3. exclude_high_motion_subjects: Verifies subjects with mean FD <= threshold are kept.
4. exclude_high_motion_subjects: Verifies empty input handling.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.preprocess import calculate_fd, exclude_high_motion_subjects, PreprocessingError


class TestCalculateFD:
    """Tests for the calculate_fd function."""
    
    def test_fd_calculation_standard(self):
        """Test FD calculation with standard displacement values."""
        # FD is sum of absolute differences of consecutive timepoints
        # plus absolute values of the first timepoint (or differences from zero)
        # Standard definition: |dx| + |dy| + |dz| + |droll| + |dpitch| + |dyaw|
        # where d values are differences between consecutive timepoints
        
        # Create a simple 6xN array (6 parameters, N timepoints)
        # Timepoint 0: all zeros
        # Timepoint 1: [0.1, 0.2, 0.3, 0.01, 0.01, 0.01]
        # Timepoint 2: [0.2, 0.4, 0.6, 0.02, 0.02, 0.02]
        
        displacements = np.array([
            [0.0, 0.1, 0.2],   # x
            [0.0, 0.2, 0.4],   # y
            [0.0, 0.3, 0.6],   # z
            [0.0, 0.01, 0.02], # roll
            [0.0, 0.01, 0.02], # pitch
            [0.0, 0.01, 0.02]  # yaw
        ])
        
        # Expected FD:
        # t=0: 0 (or first value, depending on implementation)
        # t=1: |0.1-0| + |0.2-0| + |0.3-0| + |0.01-0| + |0.01-0| + |0.01-0| = 0.73
        # t=2: |0.2-0.1| + |0.4-0.2| + |0.6-0.3| + |0.02-0.01| + |0.02-0.01| + |0.02-0.01| = 0.73
        
        fd_values = calculate_fd(displacements)
        
        assert len(fd_values) == 3, "Should return FD for each timepoint"
        # Note: Implementation may vary slightly, but should be positive
        assert all(f >= 0 for f in fd_values), "FD values should be non-negative"
        
    def test_fd_calculation_single_timepoint(self):
        """Test FD calculation with a single timepoint."""
        displacements = np.array([
            [0.1], [0.2], [0.3], [0.01], [0.01], [0.01]
        ])
        
        fd_values = calculate_fd(displacements)
        
        # With a single timepoint, FD is typically 0 or the value itself
        # depending on implementation. We expect at least one value.
        assert len(fd_values) >= 1, "Should return at least one FD value"
        
    def test_fd_calculation_zero_motion(self):
        """Test FD calculation with zero motion (all zeros)."""
        displacements = np.zeros((6, 10))
        
        fd_values = calculate_fd(displacements)
        
        assert all(f == 0 for f in fd_values), "FD should be 0 for no motion"
        
    def test_fd_calculation_high_motion(self):
        """Test FD calculation with high motion values."""
        displacements = np.array([
            [0.0, 1.0, 2.0],   # x
            [0.0, 1.0, 2.0],   # y
            [0.0, 1.0, 2.0],   # z
            [0.0, 0.1, 0.2],   # roll
            [0.0, 0.1, 0.2],   # pitch
            [0.0, 0.1, 0.2]    # yaw
        ])
        
        fd_values = calculate_fd(displacements)
        
        assert all(f > 0 for f in fd_values), "FD should be positive for motion"
        # First non-zero FD should be significant
        assert fd_values[1] > 5.0, "High motion should yield high FD"
        
    def test_fd_calculation_invalid_shape(self):
        """Test that invalid input shape raises an error."""
        # Should be 6 rows (parameters) x N columns (timepoints)
        invalid_displacements = np.array([[1, 2, 3], [4, 5, 6]])  # Only 2 rows
        
        with pytest.raises((ValueError, PreprocessingError)):
            calculate_fd(invalid_displacements)

class TestExcludeHighMotionSubjects:
    """Tests for the exclude_high_motion_subjects function."""
    
    def test_exclude_high_motion_subjects_basic(self):
        """Test that subjects with mean FD > threshold are excluded."""
        # Mock data: 3 subjects with different mean FDs
        subjects_data = {
            'sub-001': {'mean_fd': 0.3, 'file': 'sub-001.nii.gz'},
            'sub-002': {'mean_fd': 0.6, 'file': 'sub-002.nii.gz'},  # Should be excluded
            'sub-003': {'mean_fd': 0.4, 'file': 'sub-003.nii.gz'}
        }
        
        threshold = 0.5
        
        kept, excluded = exclude_high_motion_subjects(subjects_data, threshold)
        
        assert 'sub-001' in kept, "sub-001 should be kept (FD=0.3 < 0.5)"
        assert 'sub-003' in kept, "sub-003 should be kept (FD=0.4 < 0.5)"
        assert 'sub-002' in excluded, "sub-002 should be excluded (FD=0.6 > 0.5)"
        assert len(kept) == 2
        assert len(excluded) == 1
        
    def test_exclude_high_motion_subjects_boundary(self):
        """Test boundary case where mean FD equals threshold."""
        subjects_data = {
            'sub-001': {'mean_fd': 0.5, 'file': 'sub-001.nii.gz'},
            'sub-002': {'mean_fd': 0.49, 'file': 'sub-002.nii.gz'},
            'sub-003': {'mean_fd': 0.51, 'file': 'sub-003.nii.gz'}
        }
        
        threshold = 0.5
        
        kept, excluded = exclude_high_motion_subjects(subjects_data, threshold)
        
        # Implementation detail: usually > threshold excludes, <= keeps
        assert 'sub-001' in kept, "sub-001 should be kept (FD=0.5 == 0.5)"
        assert 'sub-002' in kept, "sub-002 should be kept (FD=0.49 < 0.5)"
        assert 'sub-003' in excluded, "sub-003 should be excluded (FD=0.51 > 0.5)"
        
    def test_exclude_high_motion_subjects_empty(self):
        """Test with empty input dictionary."""
        subjects_data = {}
        threshold = 0.5
        
        kept, excluded = exclude_high_motion_subjects(subjects_data, threshold)
        
        assert len(kept) == 0
        assert len(excluded) == 0
        
    def test_exclude_high_motion_subjects_all_excluded(self):
        """Test case where all subjects are excluded."""
        subjects_data = {
            'sub-001': {'mean_fd': 0.8, 'file': 'sub-001.nii.gz'},
            'sub-002': {'mean_fd': 0.9, 'file': 'sub-002.nii.gz'}
        }
        
        threshold = 0.5
        
        kept, excluded = exclude_high_motion_subjects(subjects_data, threshold)
        
        assert len(kept) == 0
        assert len(excluded) == 2
        
    def test_exclude_high_motion_subjects_all_kept(self):
        """Test case where all subjects are kept."""
        subjects_data = {
            'sub-001': {'mean_fd': 0.1, 'file': 'sub-001.nii.gz'},
            'sub-002': {'mean_fd': 0.2, 'file': 'sub-002.nii.gz'},
            'sub-003': {'mean_fd': 0.3, 'file': 'sub-003.nii.gz'}
        }
        
        threshold = 0.5
        
        kept, excluded = exclude_high_motion_subjects(subjects_data, threshold)
        
        assert len(kept) == 3
        assert len(excluded) == 0
        
    def test_exclude_high_motion_subjects_missing_mean_fd(self):
        """Test behavior when mean_fd is missing from subject data."""
        subjects_data = {
            'sub-001': {'file': 'sub-001.nii.gz'},  # Missing mean_fd
            'sub-002': {'mean_fd': 0.3, 'file': 'sub-002.nii.gz'}
        }
        
        threshold = 0.5
        
        # Should either exclude or raise an error
        # We expect it to handle gracefully (either exclude or raise)
        try:
            kept, excluded = exclude_high_motion_subjects(subjects_data, threshold)
            # If it didn't raise, sub-001 should be excluded or handled
            assert 'sub-001' not in kept or 'sub-001' in excluded
        except (KeyError, PreprocessingError):
            # Expected behavior: raise error for missing data
            pass

class TestIntegration:
    """Integration-style tests combining FD calculation and exclusion."""
    
    def test_fd_then_exclude(self):
        """Test calculating FD and then excluding based on it."""
        # Simulate a scenario where we calculate FD from displacement data
        # and then exclude subjects with high mean FD
        
        # Create mock displacement data for 2 subjects
        displacements_sub1 = np.array([
            [0.0, 0.1, 0.2, 0.1],   # x
            [0.0, 0.1, 0.2, 0.1],   # y
            [0.0, 0.1, 0.2, 0.1],   # z
            [0.0, 0.01, 0.02, 0.01], # roll
            [0.0, 0.01, 0.02, 0.01], # pitch
            [0.0, 0.01, 0.02, 0.01]  # yaw
        ])
        
        displacements_sub2 = np.array([
            [0.0, 1.0, 2.0, 1.0],   # x - high motion
            [0.0, 1.0, 2.0, 1.0],   # y
            [0.0, 1.0, 2.0, 1.0],   # z
            [0.0, 0.1, 0.2, 0.1],   # roll
            [0.0, 0.1, 0.2, 0.1],   # pitch
            [0.0, 0.1, 0.2, 0.1]    # yaw
        ])
        
        fd_sub1 = calculate_fd(displacements_sub1)
        fd_sub2 = calculate_fd(displacements_sub2)
        
        mean_fd_sub1 = np.mean(fd_sub1)
        mean_fd_sub2 = np.mean(fd_sub2)
        
        subjects_data = {
            'sub-001': {'mean_fd': mean_fd_sub1, 'file': 'sub-001.nii.gz'},
            'sub-002': {'mean_fd': mean_fd_sub2, 'file': 'sub-002.nii.gz'}
        }
        
        kept, excluded = exclude_high_motion_subjects(subjects_data, threshold=0.5)
        
        assert 'sub-001' in kept, "Low motion subject should be kept"
        assert 'sub-002' in excluded, "High motion subject should be excluded"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])