"""
Tests for motion filtering functionality (T015).
"""
import os
import tempfile
import pandas as pd
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from code.utils.motion import (
    calculate_mean_fd,
    check_motion_exclusion,
    run_motion_filtering_pipeline,
    generate_exclusion_log
)
from code.data.paths import get_processed_path, get_exclusion_log_path

class TestCalculateMeanFD:
    """Tests for Mean FD calculation."""
    
    def test_simple_motion_params(self):
        """Test Mean FD calculation with simple motion parameters."""
        # Create simple motion data: 10 timepoints, 6 parameters
        # First 5 have no motion, next 5 have motion
        motion_params = np.zeros((10, 6))
        # Add some translation in the last 5 volumes
        motion_params[5:, 0] = 0.5  # 0.5 mm translation
        
        mean_fd = calculate_mean_fd(motion_params)
        
        # Should be non-zero due to the motion
        assert mean_fd > 0.0
        # Should be less than the max motion
        assert mean_fd < 1.0
        
    def test_no_motion(self):
        """Test Mean FD with no motion (all zeros)."""
        motion_params = np.zeros((20, 6))
        mean_fd = calculate_mean_fd(motion_params)
        assert mean_fd == 0.0
        
    def test_invalid_shape(self):
        """Test that invalid motion parameter shape raises error."""
        motion_params = np.zeros((10, 5))  # Should be 6
        with pytest.raises(ValueError):
            calculate_mean_fd(motion_params)

class TestCheckMotionExclusion:
    """Tests for motion exclusion logic."""
    
    def test_below_threshold(self):
        """Test subject below threshold is not excluded."""
        assert check_motion_exclusion(0.15, threshold=0.2) is False
        
    def test_above_threshold(self):
        """Test subject above threshold is excluded."""
        assert check_motion_exclusion(0.25, threshold=0.2) is True
        
    def test_exactly_at_threshold(self):
        """Test subject exactly at threshold is not excluded."""
        assert check_motion_exclusion(0.2, threshold=0.2) is False

class TestMotionFilteringPipeline:
    """Tests for the full motion filtering pipeline."""
    
    def test_pipeline_creates_exclusion_log(self):
        """Test that pipeline creates exclusion log with correct columns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock input data
            input_data = {
                'Subject_ID': ['S001', 'S002', 'S003', 'S004'],
                'Mean_FD': [0.1, 0.25, 0.15, 0.3],
                'Age': [25, 30, 28, 35],
                'Sex': ['M', 'F', 'M', 'F'],
                'Flexibility_Score': [1.0, 2.0, 1.5, 2.5]
            }
            input_df = pd.DataFrame(input_data)
            input_path = os.path.join(tmpdir, 'merged_data.csv')
            input_df.to_csv(input_path, index=False)
            
            output_path = os.path.join(tmpdir, 'filtered_data.csv')
            exclusion_log_path = os.path.join(tmpdir, 'exclusion_log.csv')
            
            # Run pipeline with custom paths
            with patch('code.utils.motion.get_processed_path', return_value=tmpdir):
                with patch('code.utils.motion.get_exclusion_log_path', return_value=exclusion_log_path):
                    run_motion_filtering_pipeline(
                        input_csv_path=input_path,
                        output_csv_path=output_path,
                        threshold=0.2
                    )
            
            # Verify exclusion log exists and has correct columns
            assert os.path.exists(exclusion_log_path)
            exclusion_df = pd.read_csv(exclusion_log_path)
            
            assert 'Subject_ID' in exclusion_df.columns
            assert 'Exclusion_Reason' in exclusion_df.columns
            assert 'Mean_FD' in exclusion_df.columns
            
            # Should have 2 excluded subjects (S002 and S004)
            assert len(exclusion_df) == 2
            
            # Verify excluded subjects
            excluded_ids = set(exclusion_df['Subject_ID'].astype(str))
            assert excluded_ids == {'S002', 'S004'}
            
            # Verify all have Exclusion_Reason = 'Motion'
            assert all(exclusion_df['Exclusion_Reason'] == 'Motion')
            
    def test_pipeline_keeps_correct_subjects(self):
        """Test that pipeline keeps subjects below threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock input data
            input_data = {
                'Subject_ID': ['S001', 'S002', 'S003'],
                'Mean_FD': [0.1, 0.15, 0.25],
                'Age': [25, 30, 28],
                'Sex': ['M', 'F', 'M'],
                'Flexibility_Score': [1.0, 2.0, 1.5]
            }
            input_df = pd.DataFrame(input_data)
            input_path = os.path.join(tmpdir, 'merged_data.csv')
            input_df.to_csv(input_path, index=False)
            
            output_path = os.path.join(tmpdir, 'filtered_data.csv')
            exclusion_log_path = os.path.join(tmpdir, 'exclusion_log.csv')
            
            with patch('code.utils.motion.get_processed_path', return_value=tmpdir):
                with patch('code.utils.motion.get_exclusion_log_path', return_value=exclusion_log_path):
                    run_motion_filtering_pipeline(
                        input_csv_path=input_path,
                        output_csv_path=output_path,
                        threshold=0.2
                    )
            
            # Verify output data
            assert os.path.exists(output_path)
            output_df = pd.read_csv(output_path)
            
            # Should keep S001 and S003 (below threshold)
            assert len(output_df) == 2
            kept_ids = set(output_df['Subject_ID'].astype(str))
            assert kept_ids == {'S001', 'S002'}  # S002 has 0.15 which is below 0.2
            
    def test_no_exclusions(self):
        """Test pipeline when no subjects are excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_data = {
                'Subject_ID': ['S001', 'S002'],
                'Mean_FD': [0.1, 0.15],
                'Age': [25, 30],
                'Sex': ['M', 'F'],
                'Flexibility_Score': [1.0, 2.0]
            }
            input_df = pd.DataFrame(input_data)
            input_path = os.path.join(tmpdir, 'merged_data.csv')
            input_df.to_csv(input_path, index=False)
            
            output_path = os.path.join(tmpdir, 'filtered_data.csv')
            exclusion_log_path = os.path.join(tmpdir, 'exclusion_log.csv')
            
            with patch('code.utils.motion.get_processed_path', return_value=tmpdir):
                with patch('code.utils.motion.get_exclusion_log_path', return_value=exclusion_log_path):
                    run_motion_filtering_pipeline(
                        input_csv_path=input_path,
                        output_csv_path=output_path,
                        threshold=0.2
                    )
            
            # Exclusion log should exist with header only
            assert os.path.exists(exclusion_log_path)
            exclusion_df = pd.read_csv(exclusion_log_path)
            assert len(exclusion_df) == 0
            
            # All subjects should be in output
            output_df = pd.read_csv(output_path)
            assert len(output_df) == 2

if __name__ == '__main__':
    pytest.main([__file__, '-v'])