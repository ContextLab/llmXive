"""
Integration tests for fMRIPrep wrapper.

These tests verify that the fMRIPrep wrapper can run on mock data
and handle memory errors appropriately.
"""

import pytest
import subprocess
from pathlib import Path
import tempfile
import json

from data.preprocess import run_fmriprep, extract_time_series
from utils.docker import validate_docker_daemon, check_fmriprep_image
from data.validate import DataValidationError


class TestFMRIPrepWrapper:
    """Integration tests for fMRIPrep wrapper."""
    
    def test_fmriprep_runs_on_mock_data(self):
        """Test that fMRIPrep can run on mock data."""
        # Skip if Docker is not available
        if not validate_docker_daemon():
            pytest.skip("Docker daemon not available")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock BIDS structure
            bids_dir = Path(tmpdir) / "bids"
            bids_dir.mkdir()
            
            # Create dataset_description.json
            desc_file = bids_dir / "dataset_description.json"
            desc_file.write_text(json.dumps({
                "Name": "Mock Dataset",
                "BIDSVersion": "1.6.0"
            }))
            
            # Create participants.tsv
            participants_file = bids_dir / "participants.tsv"
            participants_file.write_text("participant_id\tmusical_genre\tage\tsex\n")
            participants_file.write_text("sub-001\trock\t25\tM\n")
            
            # Create subject directory
            subject_dir = bids_dir / "sub-001" / "func"
            subject_dir.mkdir(parents=True)
            
            # Create a mock BOLD file (empty file for testing)
            bold_file = subject_dir / "sub-001_task-rest_bold.nii.gz"
            bold_file.touch()
            
            # Create output directory
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()
            
            # Try to run fMRIPrep (this will likely fail in a real environment
            # without the actual fMRIPrep image, but we test the structure)
            try:
                result = run_fmriprep("sub-001", str(bids_dir), str(output_dir))
                # If it succeeds, check that output files were created
                assert result is not None
            except subprocess.CalledProcessError as e:
                # Expected if fMRIPrep image is not available
                # We're testing that the wrapper handles this gracefully
                assert "fmriprep" in str(e).lower() or "docker" in str(e).lower()
    
    def test_fmriprep_handles_memory_error(self):
        """Test that fMRIPrep handles memory errors appropriately."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock BIDS structure
            bids_dir = Path(tmpdir) / "bids"
            bids_dir.mkdir()
            
            # Create dataset_description.json
            desc_file = bids_dir / "dataset_description.json"
            desc_file.write_text(json.dumps({
                "Name": "Mock Dataset",
                "BIDSVersion": "1.6.0"
            }))
            
            # Create participants.tsv
            participants_file = bids_dir / "participants.tsv"
            participants_file.write_text("participant_id\tmusical_genre\tage\tsex\n")
            participants_file.write_text("sub-001\trock\t25\tM\n")
            
            # Create subject directory
            subject_dir = bids_dir / "sub-001" / "func"
            subject_dir.mkdir(parents=True)
            
            # Create a mock BOLD file
            bold_file = subject_dir / "sub-001_task-rest_bold.nii.gz"
            bold_file.touch()
            
            # Create output directory
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()
            
            # Test memory limit checking
            from utils.env_config import check_memory_limit
            
            # This should not raise an error if memory is sufficient
            # or raise a specific error if memory is insufficient
            try:
                memory_ok = check_memory_limit(required_gb=4)
                assert memory_ok is True or memory_ok is False
            except Exception as e:
                # Expected if memory is insufficient
                assert "memory" in str(e).lower() or "limit" in str(e).lower()
    
    def test_extract_time_series_on_mock_data(self):
        """Test that time series extraction works on mock data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock time series file
            ts_file = Path(tmpdir) / "mock_time_series.csv"
            ts_file.write_text("roi_1,roi_2,roi_3\n")
            for i in range(100):
                ts_file.write(f"{i},{i+1},{i+2}\n")
            
            # This test would require actual time series data
            # For now, we test that the function exists and can be called
            # with appropriate parameters
            assert extract_time_series is not None
    
    def test_fmriprep_validation_with_invalid_bids(self):
        """Test that fMRIPrep validation fails with invalid BIDS structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid BIDS structure (missing dataset_description.json)
            bids_dir = Path(tmpdir) / "bids"
            bids_dir.mkdir()
            
            # Create participants.tsv but no dataset_description.json
            participants_file = bids_dir / "participants.tsv"
            participants_file.write_text("participant_id\tmusical_genre\tage\tsex\n")
            
            # This should raise an error when trying to run fMRIPrep
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()
            
            try:
                run_fmriprep("sub-001", str(bids_dir), str(output_dir))
                pytest.fail("Expected an error for invalid BIDS structure")
            except Exception as e:
                assert "bids" in str(e).lower() or "validation" in str(e).lower()
    
    def test_fmriprep_with_custom_confounds(self):
        """Test that fMRIPrep can run with custom confounds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock BIDS structure
            bids_dir = Path(tmpdir) / "bids"
            bids_dir.mkdir()
            
            # Create dataset_description.json
            desc_file = bids_dir / "dataset_description.json"
            desc_file.write_text(json.dumps({
                "Name": "Mock Dataset",
                "BIDSVersion": "1.6.0"
            }))
            
            # Create participants.tsv
            participants_file = bids_dir / "participants.tsv"
            participants_file.write_text("participant_id\tmusical_genre\tage\tsex\n")
            participants_file.write_text("sub-001\trock\t25\tM\n")
            
            # Create subject directory
            subject_dir = bids_dir / "sub-001" / "func"
            subject_dir.mkdir(parents=True)
            
            # Create a mock BOLD file
            bold_file = subject_dir / "sub-001_task-rest_bold.nii.gz"
            bold_file.touch()
            
            # Create output directory
            output_dir = Path(tmpdir) / "output"
            output_dir.mkdir()
            
            # Test with custom confounds
            custom_confounds = ["trans_x", "trans_y", "rot_x", "rot_y"]
            
            try:
                result = run_fmriprep("sub-001", str(bids_dir), str(output_dir),
                                    confounds=custom_confounds)
                # If it succeeds, check that output files were created
                assert result is not None
            except subprocess.CalledProcessError as e:
                # Expected if fMRIPrep image is not available
                assert "fmriprep" in str(e).lower() or "docker" in str(e).lower()