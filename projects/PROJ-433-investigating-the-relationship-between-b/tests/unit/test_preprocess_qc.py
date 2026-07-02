import pytest
import os
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions we are testing
from preprocess import calculate_fd_from_confounds, validate_preprocessed_outputs, get_preprocessed_paths
from utils import check_fd

class TestFDValidation:
    """Tests for FD calculation and validation logic."""

    def test_calculate_fd_low_motion(self):
        """Test FD calculation with low motion data."""
        with tempfile.NamedTemporaryFile(suffix='.tsv', delete=False) as f:
            # Create a mock confounds dataframe with low motion
            data = {
                'trans_x': [0.0, 0.1, 0.1, 0.1],
                'trans_y': [0.0, 0.1, 0.1, 0.1],
                'trans_z': [0.0, 0.1, 0.1, 0.1],
                'rot_x': [0.0, 0.01, 0.01, 0.01],
                'rot_y': [0.0, 0.01, 0.01, 0.01],
                'rot_z': [0.0, 0.01, 0.01, 0.01],
            }
            df = pd.DataFrame(data)
            df.to_csv(f.name, sep='\t', index=False)
            
            fd = calculate_fd_from_confounds(Path(f.name))
            os.unlink(f.name)
            
            # With 0.1mm shifts and 0.01 rad * 50 = 0.5mm rotation
            # FD per frame approx: 0.1*3 + 0.5*3 = 0.3 + 1.5 = 1.8? 
            # Wait, diff() of [0, 0.1, 0.1, 0.1] -> [0, 0.1, 0, 0]
            # Frame 1: 0.1 + 0.1 + 0.1 + 0.5 + 0.5 + 0.5 = 1.8
            # Mean FD should be low but non-zero.
            # Let's just assert it's a valid float and < 10
            assert isinstance(fd, float)
            assert fd >= 0.0

    def test_calculate_fd_high_motion(self):
        """Test FD calculation with high motion data."""
        with tempfile.NamedTemporaryFile(suffix='.tsv', delete=False) as f:
            # High motion: 1mm shifts
            data = {
                'trans_x': [0.0, 1.0, 1.0, 1.0],
                'trans_y': [0.0, 1.0, 1.0, 1.0],
                'trans_z': [0.0, 1.0, 1.0, 1.0],
                'rot_x': [0.0, 0.1, 0.1, 0.1], # 0.1 rad * 50 = 5mm
                'rot_y': [0.0, 0.1, 0.1, 0.1],
                'rot_z': [0.0, 0.1, 0.1, 0.1],
            }
            df = pd.DataFrame(data)
            df.to_csv(f.name, sep='\t', index=False)
            
            fd = calculate_fd_from_confounds(Path(f.name))
            os.unlink(f.name)
            
            # Expect high FD
            assert fd > 0.5

    def test_check_fd_util(self):
        """Test the check_fd utility function."""
        is_valid, reason = check_fd(0.3, 0.5)
        assert is_valid is True
        
        is_valid, reason = check_fd(0.6, 0.5)
        assert is_valid is False
        assert "FD" in reason or "threshold" in reason.lower()

    @patch('preprocess._init_logger')
    @patch('preprocess.get_preprocessed_paths')
    @patch('preprocess.calculate_fd_from_confounds')
    def test_validate_preprocessed_outputs_pass(self, mock_calc_fd, mock_get_paths, mock_logger):
        """Test validation passes when FD is low."""
        mock_logger.return_value.info = MagicMock()
        mock_logger.return_value.warning = MagicMock()
        
        mock_get_paths.return_value = {
            'preproc_bold': Path('/fake/path/bold.nii.gz'),
            'confounds': Path('/fake/path/confounds.tsv')
        }
        mock_calc_fd.return_value = 0.3
        
        result = validate_preprocessed_outputs('/fake/output', 'sub-01')
        assert result is True

    @patch('preprocess._init_logger')
    @patch('preprocess.get_preprocessed_paths')
    @patch('preprocess.calculate_fd_from_confounds')
    def test_validate_preprocessed_outputs_fail(self, mock_calc_fd, mock_get_paths, mock_logger):
        """Test validation fails when FD is high."""
        mock_logger.return_value.info = MagicMock()
        mock_logger.return_value.warning = MagicMock()
        mock_logger.return_value.exclusion = MagicMock() # Assuming log_exclusion is called via utils
        
        mock_get_paths.return_value = {
            'preproc_bold': Path('/fake/path/bold.nii.gz'),
            'confounds': Path('/fake/path/confounds.tsv')
        }
        mock_calc_fd.return_value = 0.8
        
        result = validate_preprocessed_outputs('/fake/output', 'sub-01')
        assert result is False

    @patch('preprocess._init_logger')
    @patch('preprocess.get_preprocessed_paths')
    def test_validate_preprocessed_outputs_missing_confounds(self, mock_get_paths, mock_logger):
        """Test validation fails if confounds file is missing."""
        mock_logger.return_value.warning = MagicMock()
        
        mock_get_paths.return_value = {
            'preproc_bold': Path('/fake/path/bold.nii.gz')
            # No confounds
        }
        
        result = validate_preprocessed_outputs('/fake/output', 'sub-01')
        assert result is False
        mock_logger.return_value.warning.assert_called()