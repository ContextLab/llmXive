import os
import json
import tempfile
import pytest
from pathlib import Path
import pandas as pd
from preprocessing.download import check_motion_parameters_exist, save_motion_params_check_result, run_motion_params_check_pipeline

class TestMotionParamsCheck:
    """Unit tests for motion parameters checking functionality."""

    def test_motion_params_check_with_confounds_files(self):
        """Test detection of motion parameters when confounds files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a fake dataset structure with confounds file
            func_dir = Path(tmpdir) / "sub-01" / "func"
            func_dir.mkdir(parents=True)
            
            # Create a fake confounds file
            confounds_file = func_dir / "sub-01_task-rest_confounds.tsv"
            confounds_file.write_text("trans_x\ttrans_y\ttrans_z\n0.1\t0.2\t0.3\n")
            
            # Test the function
            result = check_motion_parameters_exist(tmpdir)
            assert result is True, "Should detect motion parameters in confounds file"

    def test_motion_params_check_without_motion_files(self):
        """Test detection returns False when no motion files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a fake dataset structure without motion files
            func_dir = Path(tmpdir) / "sub-01" / "func"
            func_dir.mkdir(parents=True)
            
            # Create a fake nifti file (no motion params)
            nifti_file = func_dir / "sub-01_task-rest_bold.nii.gz"
            nifti_file.write_text("fake nifti content")
            
            # Test the function
            result = check_motion_parameters_exist(tmpdir)
            assert result is False, "Should not detect motion parameters when none exist"

    def test_motion_params_check_with_participants_motion_columns(self):
        """Test detection when motion columns exist in participants.tsv."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create participants.tsv with motion columns
            participants_file = Path(tmpdir) / "participants.tsv"
            df = pd.DataFrame({
                'participant_id': ['sub-01', 'sub-02'],
                'framewise_displacement': [0.5, 0.3],
                'mean_motion': [0.2, 0.1]
            })
            df.to_csv(participants_file, sep='\t', index=False)
            
            # Test the function
            result = check_motion_parameters_exist(tmpdir)
            assert result is True, "Should detect motion parameters in participants.tsv"

    def test_save_motion_params_check_result(self):
        """Test saving motion parameters check result to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "motion_params_available.json"
            
            # Save result
            save_motion_params_check_result(True)
            
            # Verify file exists and contains correct data
            assert output_file.exists(), "Output file should exist"
            
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            assert data['motion_params_available'] is True, "JSON should contain correct value"

    def test_run_motion_params_check_pipeline(self):
        """Test the complete motion parameters check pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a fake dataset with motion files
            func_dir = Path(tmpdir) / "sub-01" / "func"
            func_dir.mkdir(parents=True)
            
            confounds_file = func_dir / "sub-01_task-rest_confounds.tsv"
            confounds_file.write_text("trans_x\ttrans_y\ttrans_z\n0.1\t0.2\t0.3\n")
            
            # Run pipeline
            result = run_motion_params_check_pipeline(tmpdir)
            
            # Verify result
            assert result is True, "Pipeline should detect motion parameters"
            
            # Verify output file was created
            output_file = Path("data/metadata/motion_params_available.json")
            assert output_file.exists(), "Output JSON file should be created"
            
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            assert data['motion_params_available'] is True, "JSON should contain correct value"

    def test_motion_params_check_nonexistent_path(self):
        """Test handling of non-existent dataset path."""
        result = check_motion_parameters_exist("/nonexistent/path")
        assert result is False, "Should return False for non-existent path"
