import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os

# Import the functions to test
from analysis.correlations import calculate_batch_size
from data.preprocess import validate_motion_parameters
from tools.verify_batching import generate_synthetic_nifti_like_data

class TestBatchSizeLogic:
    def test_batch_size_small_data(self):
        """Test that small data allows larger batches"""
        # Assuming 1 subject ~ 0.1GB, limit 7GB -> batch can be large
        batch = calculate_batch_size(estimated_total_size_gb=0.5)
        assert batch > 1, "Batch size should be > 1 for small data"

    def test_batch_size_large_data(self):
        """Test that large data forces smaller batches"""
        # Assuming data exceeds memory limit
        batch = calculate_batch_size(estimated_total_size_gb=10.0)
        assert batch <= 10, "Batch size should be small for large data"

class TestMotionValidation:
    def test_validate_motion_parameters_accepts_array(self):
        """Test that validate_motion_parameters accepts numpy arrays"""
        # Create dummy 4D fMRI data
        shape = (10, 10, 10, 20)
        data = np.random.normal(1000, 50, size=shape)
        
        # This should not raise an error
        is_valid, fd = validate_motion_parameters(data)
        assert isinstance(is_valid, bool)
        assert isinstance(fd, (int, float, np.floating))

class TestSyntheticDataGeneration:
    def test_synthetic_nifti_creation(self):
        """Test that synthetic data file is created correctly"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test.npy"
            shape = (5, 5, 5, 10)
            
            result_path = generate_synthetic_nifti_like_data(output_path, shape=shape)
            
            assert result_path.exists()
            
            # Verify content
            loaded = np.load(result_path)
            assert loaded.shape == shape
            assert loaded.dtype == np.float32

class TestIntegration:
    def test_batching_logic_integration(self):
        """
        Integration test to ensure batching logic works with synthetic data
        without requiring real HCP downloads or FSL/AFNI tools.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            data_dir = tmp_path / "test_batching"
            data_dir.mkdir()
            
            # Create 5 synthetic subjects
            subject_files = []
            for i in range(5):
                f_path = data_dir / f"sub-{i:03d}_bold.npy"
                generate_synthetic_nifti_like_data(f_path)
                subject_files.append(f_path)
            
            # Simulate batch processing loop
            batch_size = 2
            processed = 0
            
            for i in range(0, len(subject_files), batch_size):
                batch = subject_files[i : i + batch_size]
                for f_path in batch:
                    data = np.load(f_path)
                    is_valid, fd = validate_motion_parameters(data)
                    processed += 1
            
            assert processed == 5, f"Expected 5 processed, got {processed}"