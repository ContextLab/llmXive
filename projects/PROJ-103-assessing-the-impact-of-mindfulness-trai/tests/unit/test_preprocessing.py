"""
Unit tests for the preprocessing pipeline components.

These tests verify the functionality of:
- fMRIPrep runner configuration and command building
- Motion parameter extraction
- Motion filtering and exclusion logic
- Design verification integration

Run with: pytest tests/unit/test_preprocessing.py -v
"""
import os
import tempfile
import json
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest
import pandas as pd
import numpy as np

from src.preprocessing.fmriprep_runner import (
    FMRIPrepRunnerError,
    get_fmriprep_config,
    build_fmriprep_command,
    run_fmriprep
)
from src.preprocessing.extract_motion import (
    MotionExtractionError,
    find_fmriprep_confounds,
    extract_subject_id_from_path,
    extract_motion_parameters,
    write_motion_csv
)
from src.preprocessing.motion_filter import (
    MotionFilterError,
    load_motion_data,
    calculate_max_displacement,
    filter_subjects,
    write_exclusion_report
)
from src.datasets.verify_design import (
    DesignVerificationError,
    validate_metadata_fields,
    validate_design_logic,
    verify_dataset_design
)
from src.config.env import get_data_dir


# --- Fixtures ---

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def mock_motion_csv(temp_dir):
    """Create a mock motion CSV file with realistic parameters."""
    data = {
        'subject_id': ['sub-01', 'sub-02', 'sub-03', 'sub-04'],
        'translation_x': [1.0, 4.5, 0.5, 2.0],
        'translation_y': [0.5, 1.0, 3.5, 0.8],
        'translation_z': [0.2, 0.3, 0.1, 0.4],
        'rotation_x': [0.01, 0.02, 0.05, 0.01],
        'rotation_y': [0.02, 0.03, 0.01, 0.02],
        'rotation_z': [0.01, 0.04, 0.02, 0.01]
    }
    csv_path = temp_dir / "motion_params.csv"
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture
def mock_fmriprep_output(temp_dir):
    """Create a mock fMRIPrep output directory structure."""
    # Create subject directory
    sub_dir = temp_dir / "sub-01" / "func"
    sub_dir.mkdir(parents=True)
    
    # Create confounds file
    confounds_file = sub_dir / "sub-01_task-rest_desc-confounds_timeseries.tsv"
    # Create minimal TSV content
    with open(confounds_file, 'w') as f:
        f.write("trans_x\ttrans_y\ttrans_z\trot_x\trot_y\trot_z\n")
        f.write("0.1\t0.2\t0.3\t0.01\t0.02\t0.03\n")
        f.write("0.15\t0.25\t0.35\t0.015\t0.025\t0.035\n")
    
    return temp_dir

@pytest.fixture
def mock_design_json(temp_dir):
    """Create a mock design verification JSON file."""
    design_data = {
        "dataset_id": "ds000001",
        "pre_scan_count": 5,
        "post_scan_count": 5,
        "intervention_type": "mindfulness",
        "scan_type": "rs-fMRI"
    }
    design_file = temp_dir / "design.json"
    with open(design_file, 'w') as f:
        json.dump(design_data, f)
    return design_file


# --- Tests for fMRIPrep Runner ---

class TestFMRIPrepConfig:
    """Tests for fMRIPrep configuration management."""

    def test_get_fmriprep_config_defaults(self, monkeypatch):
        """Test that default config is returned when no env vars are set."""
        # Clear any existing config
        monkeypatch.delenv('FMRIPREP_THREADS', raising=False)
        monkeypatch.delenv('FMRIPREP_MEMORY', raising=False)
        
        config = get_fmriprep_config()
        
        assert 'threads' in config
        assert 'memory' in config
        assert isinstance(config['threads'], int)
        assert isinstance(config['memory'], int)

    def test_get_fmriprep_config_from_env(self, monkeypatch):
        """Test config reading from environment variables."""
        monkeypatch.setenv('FMRIPREP_THREADS', '4')
        monkeypatch.setenv('FMRIPREP_MEMORY', '16')
        
        config = get_fmriprep_config()
        
        assert config['threads'] == 4
        assert config['memory'] == 16

    def test_build_fmriprep_command_basic(self, temp_dir):
        """Test building a basic fMRIPrep command."""
        config = {
            'threads': 2,
            'memory': 8,
            'output_dir': str(temp_dir / "output"),
            'participant_label': '01'
        }
        
        cmd = build_fmriprep_command(
            input_dir=str(temp_dir / "input"),
            output_dir=config['output_dir'],
            config=config
        )
        
        assert 'fmriprep' in cmd[0]
        assert '--nthreads' in cmd
        assert '2' in cmd
        assert '--mem-mb' in cmd
        assert '8' in cmd

    def test_run_fmriprep_success(self, temp_dir):
        """Test successful fMRIPrep execution (mocked)."""
        with patch('src.preprocessing.fmriprep_runner.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            config = {
                'threads': 2,
                'memory': 8,
                'output_dir': str(temp_dir / "output")
            }
            
            result = run_fmriprep(
                input_dir=str(temp_dir / "input"),
                output_dir=config['output_dir'],
                config=config
            )
            
            assert result['success'] is True
            assert result['returncode'] == 0

    def test_run_fmriprep_failure(self, temp_dir):
        """Test fMRIPrep execution failure handling."""
        with patch('src.preprocessing.fmriprep_runner.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="Error message")
            
            config = {
                'threads': 2,
                'memory': 8,
                'output_dir': str(temp_dir / "output")
            }
            
            with pytest.raises(FMRIPrepRunnerError):
                run_fmriprep(
                    input_dir=str(temp_dir / "input"),
                    output_dir=config['output_dir'],
                    config=config
                )


# --- Tests for Motion Extraction ---

class TestMotionExtraction:
    """Tests for motion parameter extraction from fMRIPrep outputs."""

    def test_extract_subject_id_from_path(self):
        """Test subject ID extraction from file paths."""
        path1 = "/data/sub-01/func/sub-01_task-rest_bold.nii.gz"
        path2 = "/data/sub-02/func/sub-02_task-rest_desc-confounds_timeseries.tsv"
        
        assert extract_subject_id_from_path(path1) == "sub-01"
        assert extract_subject_id_from_path(path2) == "sub-02"

    def test_find_fmriprep_confounds(self, mock_fmriprep_output):
        """Test finding confound files in fMRIPrep output."""
        confounds = find_fmriprep_confounds(mock_fmriprep_output / "sub-01")
        
        assert len(confounds) > 0
        assert any("confounds" in str(f) for f in confounds)

    def test_extract_motion_parameters_valid(self, mock_fmriprep_output):
        """Test extracting motion parameters from valid confound file."""
        confounds_path = mock_fmriprep_output / "sub-01" / "func" / "sub-01_task-rest_desc-confounds_timeseries.tsv"
        
        motion_params = extract_motion_parameters(confounds_path)
        
        assert 'translation_x' in motion_params
        assert 'translation_y' in motion_params
        assert 'translation_z' in motion_params
        assert 'rotation_x' in motion_params
        assert 'rotation_y' in motion_params
        assert 'rotation_z' in motion_params
        assert len(motion_params['translation_x']) > 0

    def test_write_motion_csv(self, temp_dir, mock_fmriprep_output):
        """Test writing motion parameters to CSV."""
        confounds_path = mock_fmriprep_output / "sub-01" / "func" / "sub-01_task-rest_desc-confounds_timeseries.tsv"
        motion_params = extract_motion_parameters(confounds_path)
        
        output_path = temp_dir / "motion_output.csv"
        write_motion_csv(motion_params, str(output_path), "sub-01")
        
        assert output_path.exists()
        
        # Verify CSV content
        df = pd.read_csv(output_path)
        assert 'subject_id' in df.columns
        assert len(df) == len(motion_params['translation_x'])

    def test_extract_motion_parameters_invalid_file(self, temp_dir):
        """Test handling of invalid confound file."""
        invalid_path = temp_dir / "nonexistent.tsv"
        
        with pytest.raises(MotionExtractionError):
            extract_motion_parameters(invalid_path)


# --- Tests for Motion Filtering ---

class TestMotionFiltering:
    """Tests for motion-based subject exclusion."""

    def test_load_motion_data(self, mock_motion_csv):
        """Test loading motion data from CSV."""
        data = load_motion_data(str(mock_motion_csv))
        
        assert isinstance(data, pd.DataFrame)
        assert 'subject_id' in data.columns
        assert len(data) == 4

    def test_calculate_max_displacement(self, mock_motion_csv):
        """Test calculation of maximum displacement."""
        data = load_motion_csv(str(mock_motion_csv))
        
        max_disp = calculate_max_displacement(data)
        
        assert isinstance(max_disp, dict)
        assert 'sub-01' in max_disp
        assert 'sub-02' in max_disp
        
        # sub-02 has high translation (4.5, 1.0, 0.3) -> sqrt(4.5^2 + 1^2 + 0.3^2) ≈ 4.6
        assert max_disp['sub-02'] > 4.0

    def test_filter_subjects_strict(self, mock_motion_csv):
        """Test subject filtering with strict thresholds."""
        data = load_motion_data(str(mock_motion_csv))
        
        # Thresholds: 3mm translation, 3° rotation
        included, excluded = filter_subjects(
            data, 
            translation_threshold=3.0, 
            rotation_threshold=3.0
        )
        
        assert isinstance(included, list)
        assert isinstance(excluded, list)
        
        # sub-02 should be excluded (high translation)
        assert 'sub-02' in excluded
        assert 'sub-01' in included

    def test_filter_subjects_no_exclusions(self, mock_motion_csv):
        """Test filtering when no subjects exceed thresholds."""
        data = load_motion_data(str(mock_motion_csv))
        
        included, excluded = filter_subjects(
            data,
            translation_threshold=10.0,
            rotation_threshold=10.0
        )
        
        assert len(included) == 4
        assert len(excluded) == 0

    def test_write_exclusion_report(self, temp_dir, mock_motion_csv):
        """Test writing exclusion report."""
        data = load_motion_data(str(mock_motion_csv))
        included, excluded = filter_subjects(data, translation_threshold=3.0, rotation_threshold=3.0)
        
        report_path = temp_dir / "exclusion_report.json"
        write_exclusion_report(included, excluded, str(report_path))
        
        assert report_path.exists()
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert 'included_subjects' in report
        assert 'excluded_subjects' in report
        assert 'exclusion_reasons' in report


# --- Tests for Design Verification ---

class TestDesignVerification:
    """Tests for dataset design verification."""

    def test_validate_metadata_fields_valid(self, mock_design_json):
        """Test validation with valid metadata fields."""
        with open(mock_design_json, 'r') as f:
            metadata = json.load(f)
        
        is_valid, errors = validate_metadata_fields(metadata)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_metadata_fields_missing(self, temp_dir):
        """Test validation with missing required fields."""
        incomplete_data = {
            "dataset_id": "ds000001",
            "pre_scan_count": 5
            # Missing post_scan_count, intervention_type, scan_type
        }
        
        is_valid, errors = validate_metadata_fields(incomplete_data)
        
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_design_logic_valid(self, mock_design_json):
        """Test design logic validation with valid data."""
        with open(mock_design_json, 'r') as f:
            metadata = json.load(f)
        
        is_valid, errors = validate_design_logic(metadata)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_design_logic_invalid_scans(self, temp_dir):
        """Test design logic validation with invalid scan counts."""
        invalid_data = {
            "dataset_id": "ds000001",
            "pre_scan_count": 0,
            "post_scan_count": 5,
            "intervention_type": "mindfulness",
            "scan_type": "rs-fMRI"
        }
        
        is_valid, errors = validate_design_logic(invalid_data)
        
        assert is_valid is False
        assert any("pre_scan_count" in err for err in errors)

    def test_validate_design_logic_invalid_intervention(self, temp_dir):
        """Test design logic validation with invalid intervention type."""
        invalid_data = {
            "dataset_id": "ds000001",
            "pre_scan_count": 5,
            "post_scan_count": 5,
            "intervention_type": "cognitive_training",
            "scan_type": "rs-fMRI"
        }
        
        is_valid, errors = validate_design_logic(invalid_data)
        
        assert is_valid is False
        assert any("intervention_type" in err for err in errors)

    def test_verify_dataset_design(self, mock_design_json):
        """Test full dataset design verification."""
        result = verify_dataset_design(str(mock_design_json))
        
        assert 'valid' in result
        assert 'errors' in result
        assert 'warnings' in result


# --- Integration Tests ---

class TestPreprocessingIntegration:
    """Integration tests for the preprocessing pipeline."""

    def test_end_to_end_motion_extraction(self, temp_dir, mock_fmriprep_output):
        """Test end-to-end motion extraction workflow."""
        # Step 1: Find confounds
        confounds = find_fmriprep_confounds(mock_fmriprep_output / "sub-01")
        assert len(confounds) > 0
        
        # Step 2: Extract motion parameters
        motion_params = extract_motion_parameters(confounds[0])
        assert len(motion_params['translation_x']) > 0
        
        # Step 3: Write to CSV
        output_csv = temp_dir / "final_motion.csv"
        write_motion_csv(motion_params, str(output_csv), "sub-01")
        assert output_csv.exists()

    def test_end_to_end_motion_filtering(self, temp_dir, mock_motion_csv):
        """Test end-to-end motion filtering workflow."""
        # Step 1: Load data
        data = load_motion_data(str(mock_motion_csv))
        
        # Step 2: Filter subjects
        included, excluded = filter_subjects(data, translation_threshold=3.0, rotation_threshold=3.0)
        
        # Step 3: Write report
        report_path = temp_dir / "filter_report.json"
        write_exclusion_report(included, excluded, str(report_path))
        
        assert report_path.exists()
        assert 'sub-02' in excluded  # Should be excluded due to high motion

    def test_full_design_verification_workflow(self, temp_dir):
        """Test full design verification workflow."""
        # Create valid design file
        design_data = {
            "dataset_id": "ds_test",
            "pre_scan_count": 3,
            "post_scan_count": 3,
            "intervention_type": "MBSR",
            "scan_type": "rs-fMRI"
        }
        
        design_file = temp_dir / "design.json"
        with open(design_file, 'w') as f:
            json.dump(design_data, f)
        
        # Verify design
        result = verify_dataset_design(str(design_file))
        
        assert result['valid'] is True
        assert len(result['errors']) == 0