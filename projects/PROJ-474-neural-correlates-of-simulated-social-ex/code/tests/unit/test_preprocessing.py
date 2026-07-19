"""
Unit tests for preprocessing module.
"""
import pytest
import numpy as np
import nibabel as nib
import pandas as pd
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import os

from src.preprocessing import (
    load_confounds_from_file,
    perform_nuisance_regression,
    preprocess_subject,
    is_already_preprocessed
)
from src.exceptions import DataUnavailableError

class TestPreprocessing:
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def sample_confounds(self, temp_dir):
        """Create sample confounds TSV file."""
        confounds_data = {
            'trans_x': np.random.randn(100),
            'trans_y': np.random.randn(100),
            'trans_z': np.random.randn(100),
            'rot_x': np.random.randn(100),
            'rot_y': np.random.randn(100),
            'rot_z': np.random.randn(100),
            'trans_x_derivative1': np.random.randn(100),
            'trans_y_derivative1': np.random.randn(100),
            'trans_z_derivative1': np.random.randn(100),
            'rot_x_derivative1': np.random.randn(100),
            'rot_y_derivative1': np.random.randn(100),
            'rot_z_derivative1': np.random.randn(100),
        }
        confounds_df = pd.DataFrame(confounds_data)
        confounds_path = temp_dir / 'confounds.tsv'
        confounds_df.to_csv(confounds_path, sep='\t', index=False)
        return confounds_path
    
    @pytest.fixture
    def sample_func_image(self, temp_dir):
        """Create sample functional NIfTI image."""
        # Create random 4D data (x, y, z, t)
        data = np.random.randn(10, 10, 10, 100).astype(np.float32)
        affine = np.eye(4)
        img = nib.Nifti1Image(data, affine)
        func_path = temp_dir / 'func.nii.gz'
        nib.save(img, func_path)
        return func_path
    
    def test_load_confounds_from_file(self, sample_confounds):
        """Test loading confounds from TSV file."""
        confounds = load_confounds_from_file(sample_confounds)
        
        assert confounds is not None
        assert confounds.shape[0] == 100  # n_timepoints
        assert confounds.shape[1] >= 6  # at least 6 motion params
        assert isinstance(confounds, np.ndarray)
    
    def test_load_confounds_from_file_missing(self, temp_dir):
        """Test loading confounds from non-existent file."""
        non_existent = temp_dir / 'non_existent.tsv'
        confounds = load_confounds_from_file(non_existent)
        
        assert confounds is None
    
    def test_is_already_preprocessed_newer(self, temp_dir, sample_func_image):
        """Test is_already_preprocessed when output is newer."""
        output_path = temp_dir / 'output.nii.gz'
        
        # Create output file with future timestamp
        with open(output_path, 'w') as f:
            f.write('test')
        
        # Set output time to be newer
        import time
        future_time = time.time() + 1000
        os.utime(output_path, (future_time, future_time))
        
        result = is_already_preprocessed(sample_func_image, sample_func_image, output_path)
        assert result is True
    
    def test_is_already_preprocessed_older(self, temp_dir, sample_func_image):
        """Test is_already_preprocessed when output is older."""
        output_path = temp_dir / 'output.nii.gz'
        
        # Create output file
        with open(output_path, 'w') as f:
            f.write('test')
        
        result = is_already_preprocessed(sample_func_image, sample_func_image, output_path)
        assert result is False  # Output doesn't exist or is older
    
    def test_is_already_preprocessed_not_exists(self, temp_dir, sample_func_image):
        """Test is_already_preprocessed when output doesn't exist."""
        output_path = temp_dir / 'non_existent_output.nii.gz'
        
        result = is_already_preprocessed(sample_func_image, sample_func_image, output_path)
        assert result is False
    
    @patch('src.preprocessing.get_wm_csf_masks')
    @patch('src.preprocessing.perform_nuisance_regression')
    def test_preprocess_subject(self, mock_reg, mock_masks, temp_dir, sample_func_image, sample_confounds):
        """Test preprocessing a single subject."""
        # Mock dependencies
        mock_masks.return_value = (np.ones((10, 10, 10)), np.ones((10, 10, 10)))
        mock_reg.return_value = np.random.randn(10, 10, 10, 100).astype(np.float32)
        
        config = {
            'tr': 2.0,
            'paths': {
                'processed': str(temp_dir)
            }
        }
        
        output_path = preprocess_subject(
            'sub-01',
            sample_func_image,
            sample_confounds,
            temp_dir,
            config
        )
        
        assert output_path.exists()
        assert 'preprocessed_sub-01' in str(output_path)
    
    def test_preprocess_subject_missing_confounds(self, temp_dir, sample_func_image):
        """Test preprocessing with missing confounds."""
        non_existent_confounds = temp_dir / 'non_existent.tsv'
        config = {'tr': 2.0, 'paths': {'processed': str(temp_dir)}}
        
        with pytest.raises(DataUnavailableError):
            preprocess_subject(
                'sub-01',
                sample_func_image,
                non_existent_confounds,
                temp_dir,
                config
            )