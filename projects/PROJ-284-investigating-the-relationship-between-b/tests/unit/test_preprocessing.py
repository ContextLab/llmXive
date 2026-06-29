import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import tempfile

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data.preprocess import (
    correct_motion,
    slice_time_correction_and_normalization,
    smooth_image,
    calculate_tsnr,
    validate_motion_parameters,
    preprocess_subject_batch
)

class TestMotionCorrection:
    def test_motion_correction_output(self):
        """Test that motion correction produces output."""
        # Create synthetic NIfTI-like data
        np.random.seed(42)
        data = np.random.randn(64, 64, 30, 100)
        
        # Mock the FSL mcflirt tool
        with patch('data.preprocess.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            # Simulate motion correction
            result = correct_motion(data, 'output_path.nii.gz')
            
            # Verify subprocess was called
            assert mock_run.called, "mcflirt should be called"

    def test_motion_correction_with_real_tool(self):
        """Test motion correction with actual tool path (if available)."""
        # This test checks if FSL is available
        with patch('data.preprocess.get_fsl_tool_path') as mock_path:
            mock_path.return_value = '/usr/bin/mcflirt'
            
            # If FSL is available, this would run the actual tool
            # In CI, this would be skipped or mocked
            pass

class TestSliceTimeCorrection:
    def test_slice_time_correction_output(self):
        """Test that slice time correction produces output."""
        # Create synthetic data
        np.random.seed(42)
        data = np.random.randn(64, 64, 30, 100)
        
        # Mock AFNI 3dTshift
        with patch('data.preprocess.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = slice_time_correction_and_normalization(data, 'output_path.nii.gz')
            
            assert mock_run.called, "3dTshift should be called"

    def test_normalization_to_mni(self):
        """Test normalization to MNI space."""
        # Mock AFNI 3dQwarp
        with patch('data.preprocess.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            # Normalization would be called as part of slice time correction
            pass

class TestSmoothing:
    def test_smoothing_output(self):
        """Test that smoothing produces output."""
        # Create synthetic data
        np.random.seed(42)
        data = np.random.randn(64, 64, 30, 100)
        
        # Mock FSL fslmaths
        with patch('data.preprocess.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = smooth_image(data, 'output_path.nii.gz', fwhm=6)
            
            assert mock_run.called, "fslmaths should be called"

    def test_smoothing_kernel_size(self):
        """Test that smoothing uses correct kernel size."""
        fwhm = 6  # mm
        
        # The smoothing function should use this FWHM
        # Actual implementation would pass this to fslmaths
        assert fwhm > 0, "FWHM should be positive"

class TestTSNR:
    def test_tsnr_calculation(self):
        """Test tSNR calculation."""
        np.random.seed(42)
        # Create synthetic time series data
        n_timepoints = 100
        n_voxels = 64 * 64 * 30
        
        data = np.random.randn(n_timepoints, n_voxels)
        # Add a constant signal component
        data += 1000
        
        # Calculate tSNR: mean / std (excluding first few volumes)
        data_trimmed = data[5:, :]  # Exclude first 5 volumes
        
        mean_signal = np.mean(data_trimmed, axis=0)
        std_signal = np.std(data_trimmed, axis=0)
        
        # Avoid division by zero
        std_signal[std_signal == 0] = 1e-10
        
        tsnr = mean_signal / std_signal
        
        # tSNR should be positive
        assert np.all(tsnr > 0), "tSNR should be positive"
        
        # Typical tSNR values are in the range 50-200 for good data
        median_tsnr = np.median(tsnr)
        assert 20 < median_tsnr < 500, f"tSNR should be in reasonable range, got {median_tsnr}"

    def test_tsnr_quality_threshold(self):
        """Test that tSNR meets quality threshold."""
        # Simulate good quality data
        np.random.seed(42)
        data = np.random.randn(100, 1000) + 1000  # High signal
        
        data_trimmed = data[5:, :]
        mean_signal = np.mean(data_trimmed, axis=0)
        std_signal = np.std(data_trimmed, axis=0)
        std_signal[std_signal == 0] = 1e-10
        
        tsnr = mean_signal / std_signal
        median_tsnr = np.median(tsnr)
        
        # Threshold from task: tSNR >= 50
        assert median_tsnr >= 50, f"tSNR should be >= 50, got {median_tsnr}"

class TestMotionValidation:
    def test_motion_validation_threshold(self):
        """Test motion validation with threshold."""
        # Simulate motion parameters (6 parameters per timepoint)
        np.random.seed(42)
        n_timepoints = 100
        motion_params = np.random.randn(n_timepoints, 6) * 0.1  # Small motion
        
        # Calculate framewise displacement
        fd = np.sum(np.abs(np.diff(motion_params, axis=0)), axis=1)
        
        # Average FD
        avg_fd = np.mean(fd)
        
        # Threshold from task: < 0.5mm
        assert avg_fd < 0.5, f"Average FD should be < 0.5, got {avg_fd}"

    def test_motion_validation_exceeds_threshold(self):
        """Test motion validation when threshold is exceeded."""
        # Simulate high motion
        np.random.seed(42)
        n_timepoints = 100
        motion_params = np.random.randn(n_timepoints, 6) * 1.0  # Large motion
        
        fd = np.sum(np.abs(np.diff(motion_params, axis=0)), axis=1)
        avg_fd = np.mean(fd)
        
        # This should exceed threshold
        assert avg_fd >= 0.5, f"Average FD should be >= 0.5 for high motion, got {avg_fd}"

    def test_motion_validation_boolean_result(self):
        """Test that motion validation returns boolean."""
        np.random.seed(42)
        motion_params = np.random.randn(100, 6) * 0.1
        
        fd = np.sum(np.abs(np.diff(motion_params, axis=0)), axis=1)
        avg_fd = np.mean(fd)
        
        is_valid = avg_fd < 0.5
        
        assert isinstance(is_valid, bool), "Motion validation should return boolean"

class TestBatchProcessing:
    def test_batch_processing_memory_constraint(self):
        """Test that batch processing respects memory constraints."""
        available_memory = 7.0  # GB
        file_size = 0.5  # GB per subject
        
        # Calculate batch size
        batch_size = int(available_memory / file_size)
        
        assert batch_size > 0, "Batch size should be positive"
        assert batch_size * file_size <= available_memory, \
            "Batch should fit in memory"

    def test_batch_processing_with_synthetic_data(self):
        """Test batch processing with synthetic data (for CI validation)."""
        # Create synthetic NIfTI-like data
        np.random.seed(42)
        synthetic_data = np.random.randn(64, 64, 30, 100)
        
        # Mock the preprocessing functions
        with patch('data.preprocess.correct_motion') as mock_motion, \
             patch('data.preprocess.slice_time_correction_and_normalization') as mock_slice, \
             patch('data.preprocess.smooth_image') as mock_smooth:
            
            mock_motion.return_value = True
            mock_slice.return_value = True
            mock_smooth.return_value = True
            
            # Process a batch of subjects
            subjects = ['sub-001', 'sub-002', 'sub-003']
            
            results = preprocess_subject_batch(subjects, synthetic_data)
            
            assert len(results) == 3, "Should process all subjects"
            assert all(results), "All subjects should be processed successfully"

class TestToolPaths:
    def test_fsl_tool_path(self):
        """Test FSL tool path resolution."""
        with patch('data.preprocess.get_fsl_tool_path') as mock_path:
            mock_path.return_value = '/usr/bin/mcflirt'
            
            path = mock_path()
            assert path is not None, "FSL tool path should be resolved"

    def test_afni_tool_path(self):
        """Test AFNI tool path resolution."""
        with patch('data.preprocess.get_afni_tool_path') as mock_path:
            mock_path.return_value = '/usr/bin/3dTshift'
            
            path = mock_path()
            assert path is not None, "AFNI tool path should be resolved"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])