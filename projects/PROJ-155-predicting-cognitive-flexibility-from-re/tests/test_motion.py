import os
import csv
import tempfile
import shutil
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from code.utils.motion import (
    calculate_mean_fd,
    check_motion_exclusion,
    generate_exclusion_log,
    process_subject_motion,
    run_motion_filtering_pipeline
)
from code.utils.logging import get_exclusion_log_path


class TestCalculateMeanFd:
    def test_mean_fd_calculation(self):
        """Test that Mean FD is calculated correctly."""
        # Create a simple motion parameter array (10 timepoints, 6 params)
        motion_params = np.zeros((10, 6))
        # Add some displacement in translation
        motion_params[1:, 0] = 0.1  # 0.1mm in x direction for 9 frames
        
        mean_fd = calculate_mean_fd(motion_params)
        
        # Expected: 9 frames with 0.1mm displacement -> mean = 0.1
        assert np.isclose(mean_fd, 0.1, atol=1e-6)
    
    def test_mean_fd_with_rotation(self):
        """Test Mean FD calculation including rotation."""
        motion_params = np.zeros((10, 6))
        # Add rotation: 0.01 radians (~0.5 degrees)
        # 50mm radius * 0.01 rad = 0.5mm displacement
        motion_params[1:, 3] = 0.01
        
        mean_fd = calculate_mean_fd(motion_params)
        
        # Expected: 9 frames * (50 * 0.01) = 0.5mm per frame -> mean = 0.5
        assert np.isclose(mean_fd, 0.5, atol=1e-6)
    
    def test_invalid_motion_params(self):
        """Test that invalid motion params raise an error."""
        motion_params = np.zeros((10, 4))  # Wrong number of columns
        
        with pytest.raises(ValueError):
            calculate_mean_fd(motion_params)


class TestCheckMotionExclusion:
    def test_below_threshold(self):
        """Test subject below threshold is not excluded."""
        should_exclude, reason = check_motion_exclusion(0.1, threshold=0.2)
        
        assert should_exclude is False
        assert reason == ""
    
    def test_above_threshold(self):
        """Test subject above threshold is excluded."""
        should_exclude, reason = check_motion_exclusion(0.3, threshold=0.2)
        
        assert should_exclude is True
        assert "Motion" in reason
        assert "0.3" in reason
    
    def test_default_threshold(self):
        """Test default threshold is 0.2."""
        should_exclude, _ = check_motion_exclusion(0.25)
        assert should_exclude is True


class TestGenerateExclusionLog:
    def test_write_exclusion_log(self):
        """Test that exclusion log is written correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "exclusion_log.csv")
            
            excluded_subjects = [
                {'Subject_ID': '100101', 'Exclusion_Reason': 'Motion', 'Mean_FD': 0.25},
                {'Subject_ID': '100202', 'Exclusion_Reason': 'Motion', 'Mean_FD': 0.35}
            ]
            
            generate_exclusion_log(excluded_subjects, log_path)
            
            # Verify file exists
            assert os.path.exists(log_path)
            
            # Verify contents
            with open(log_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2
            assert rows[0]['Subject_ID'] == '100101'
            assert rows[0]['Exclusion_Reason'] == 'Motion'
            assert float(rows[0]['Mean_FD']) == 0.25
            assert rows[1]['Subject_ID'] == '100202'
            assert rows[1]['Exclusion_Reason'] == 'Motion'
            assert float(rows[1]['Mean_FD']) == 0.35
    
    def test_append_to_existing_log(self):
        """Test that new exclusions are appended to existing log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "exclusion_log.csv")
            
            # Write initial log
            initial_subjects = [
                {'Subject_ID': '100101', 'Exclusion_Reason': 'Motion', 'Mean_FD': 0.25}
            ]
            generate_exclusion_log(initial_subjects, log_path)
            
            # Append more exclusions
            new_subjects = [
                {'Subject_ID': '100202', 'Exclusion_Reason': 'Motion', 'Mean_FD': 0.35}
            ]
            generate_exclusion_log(new_subjects, log_path)
            
            # Verify both entries exist
            with open(log_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2


class TestRunMotionFilteringPipeline:
    @patch('code.utils.motion.load_motion_params_from_nifti')
    @patch('code.utils.motion.calculate_mean_fd')
    @patch('code.utils.motion.check_motion_exclusion')
    def test_pipeline_includes_and_excludes(self, mock_check, mock_calc, mock_load):
        """Test that pipeline correctly includes and excludes subjects."""
        
        # Mock data
        mock_load.return_value = np.zeros((100, 6))
        mock_calc.return_value = 0.15  # Below threshold
        
        subject_ids = ['100101', '100202', '100303']
        nifti_paths = ['/fake/path1.nii', '/fake/path2.nii', '/fake/path3.nii']
        
        # First subject passes, second fails, third passes
        mock_check.side_effect = [
            (False, ""),  # 100101
            (True, "Motion"),  # 100202
            (False, "")  # 100303
        ]
        
        included, excluded = run_motion_filtering_pipeline(subject_ids, nifti_paths)
        
        assert len(included) == 2
        assert len(excluded) == 1
        assert excluded[0]['Subject_ID'] == '100202'
        assert excluded[0]['Exclusion_Reason'] == 'Motion'