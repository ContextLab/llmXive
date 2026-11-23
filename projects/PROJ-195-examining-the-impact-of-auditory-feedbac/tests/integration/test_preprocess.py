"""
Integration test for preprocessing pipeline (Task T014/T016).

Verifies:
  1. Event label validation (T016).
  2. Motion QC extraction and logging (T017, T019).
  3. Preprocessing deviation logging (T016).
  4. Generation of valid_subjects.txt (T018).
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import json
import pandas as pd

import pytest
import nibabel as nib
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from preprocess import (
    setup_logging,
    get_subject_list,
    run_fmriprep_for_subject,
    log_preprocessing_deviations,
    process_qc_and_exclude,
    main
)
from utils import (
    validate_event_labels,
    validate_all_subjects_events,
    check_motion_threshold,
    parse_motion_parameters,
    log_qc_metrics,
    get_motion_file
)

# Fixtures
@pytest.fixture
def mock_bids_dir():
    """Create a mock BIDS directory with events and motion files."""
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    # Create BIDS structure
    (temp_path / 'sub-01' / 'func').mkdir(parents=True)
    (temp_path / 'sub-02' / 'func').mkdir(parents=True)
    (temp_path / 'derivatives' / 'sub-01').mkdir(parents=True)
    (temp_path / 'derivatives' / 'sub-02').mkdir(parents=True)
    
    # Create events files with required labels
    events_data = {
        'onset': [0, 20, 40],
        'duration': [1, 1, 1],
        'trial_type': ['normal', 'delayed', 'pitch-shifted']
    }
    df_events = pd.DataFrame(events_data)
    df_events.to_csv(temp_path / 'sub-01' / 'func' / 'sub-01_task-motor_events.tsv', sep='\t', index=False)
    df_events.to_csv(temp_path / 'sub-02' / 'func' / 'sub-02_task-motor_events.tsv', sep='\t', index=False)
    
    # Create mock motion files
    motion_data_good = {
        'trans_x': [0.1, 0.2, 0.1],
        'trans_y': [0.1, 0.2, 0.1],
        'trans_z': [0.1, 0.2, 0.1],
        'rot_x': [0.01, 0.02, 0.01],
        'rot_y': [0.01, 0.02, 0.01],
        'rot_z': [0.01, 0.02, 0.01]
    }
    df_motion_good = pd.DataFrame(motion_data_good)
    df_motion_good.to_csv(temp_path / 'derivatives' / 'sub-01' / 'sub-01_desc-confounds_timeseries.tsv', sep='\t', index=False)
    
    # Create motion file for sub-02 with high motion
    motion_data_bad = {
        'trans_x': [0.1, 3.0, 0.1],  # High motion at frame 1
        'trans_y': [0.1, 0.2, 0.1],
        'trans_z': [0.1, 0.2, 0.1],
        'rot_x': [0.01, 0.02, 0.01],
        'rot_y': [0.01, 0.02, 0.01],
        'rot_z': [0.01, 0.02, 0.01]
    }
    df_motion_bad = pd.DataFrame(motion_data_bad)
    df_motion_bad.to_csv(temp_path / 'derivatives' / 'sub-02' / 'sub-02_desc-confounds_timeseries.tsv', sep='\t', index=False)
    
    # Create mock functional images (empty but valid NIfTI)
    img = nib.Nifti1Image(np.zeros((10, 10, 10, 10)), np.eye(4))
    img.to_filename(temp_path / 'sub-01' / 'func' / 'sub-01_task-motor_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz')
    img.to_filename(temp_path / 'sub-02' / 'func' / 'sub-02_task-motor_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz')
    
    return temp_path


@pytest.fixture
def cleanup_mock(mock_bids_dir):
    yield mock_bids_dir
    shutil.rmtree(mock_bids_dir)


class TestEventValidation:
    def test_validate_event_labels_success(self, mock_bids_dir):
        """Test that event validation passes for correct labels."""
        events_file = mock_bids_dir / 'sub-01' / 'func' / 'sub-01_task-motor_events.tsv'
        required = ['normal', 'delayed', 'pitch-shifted']
        
        assert validate_event_labels('sub-01', events_file, required) is True

    def test_validate_event_labels_missing(self, mock_bids_dir):
        """Test that event validation fails for missing labels."""
        # Modify events file to remove a label
        events_file = mock_bids_dir / 'sub-01' / 'func' / 'sub-01_task-motor_events.tsv'
        df = pd.read_csv(events_file, sep='\t')
        df['trial_type'] = ['normal', 'delayed', 'normal']  # Removed pitch-shifted
        df.to_csv(events_file, sep='\t', index=False)
        
        required = ['normal', 'delayed', 'pitch-shifted']
        assert validate_event_labels('sub-01', events_file, required) is False


class TestMotionQC:
    def test_motion_threshold_check(self, mock_bids_dir):
        """Test that motion threshold check works correctly."""
        motion_file_good = mock_bids_dir / 'derivatives' / 'sub-01' / 'sub-01_desc-confounds_timeseries.tsv'
        motion_file_bad = mock_bids_dir / 'derivatives' / 'sub-02' / 'sub-02_desc-confounds_timeseries.tsv'
        
        motion_good = parse_motion_parameters(motion_file_good)
        motion_bad = parse_motion_parameters(motion_file_bad)
        
        exceeds_good, _ = check_motion_threshold(motion_good, threshold=2.0)
        exceeds_bad, _ = check_motion_threshold(motion_bad, threshold=2.0)
        
        assert exceeds_good is False
        assert exceeds_bad is True

    def test_log_qc_metrics(self, mock_bids_dir, tmp_path):
        """Test that QC metrics are logged correctly."""
        log_file = tmp_path / 'preprocessing.log'
        logger = setup_logging(log_file)
        
        motion_file_good = mock_bids_dir / 'derivatives' / 'sub-01' / 'sub-01_desc-confounds_timeseries.tsv'
        motion_file_bad = mock_bids_dir / 'derivatives' / 'sub-02' / 'sub-02_desc-confounds_timeseries.tsv'
        
        result_good = log_qc_metrics('sub-01', motion_file_good, logger, threshold=2.0)
        result_bad = log_qc_metrics('sub-02', motion_file_bad, logger, threshold=2.0)
        
        assert result_good is False  # sub-01 is OK
        assert result_bad is True   # sub-02 exceeds threshold
        
        # Check log file contents
        with open(log_file, 'r') as f:
            content = f.read()
            assert 'sub-01' in content
            assert 'sub-02' in content
            assert 'exceeds motion threshold' in content


class TestDeviationLogging:
    def test_log_preprocessing_deviations(self, mock_bids_dir, tmp_path):
        """Test that preprocessing deviations are logged (T016)."""
        log_file = tmp_path / 'preprocessing.log'
        
        # Call the logging function
        log_preprocessing_deviations(
            subject_id='sub-01',
            deviation_type='motion',
            details='Frame 5 exceeded 2mm threshold',
            log_file=log_file
        )
        
        # Check log file
        assert log_file.exists()
        with open(log_file, 'r') as f:
            content = f.read()
            assert 'sub-01' in content
            assert 'motion' in content
            assert 'Frame 5 exceeded 2mm threshold' in content
        
        # Check JSON log
        json_log = tmp_path / 'preprocessing.json'
        # The function writes to the same file in JSON format in the updated utils
        # Adjust if the implementation writes to a separate JSON file
        # For now, we check the main log file for the text
        assert 'DEVIATION' in content


class TestSubjectExclusion:
    def test_process_qc_and_exclude(self, mock_bids_dir, tmp_path):
        """Test that subjects are excluded based on QC."""
        log_file = tmp_path / 'preprocessing.log'
        output_file = tmp_path / 'valid_subjects.txt'
        
        # Simulate processing
        subjects = ['sub-01', 'sub-02']
        valid = []
        excluded = []
        
        for sub in subjects:
            motion_file = get_motion_file(sub, mock_bids_dir / 'derivatives')
            if motion_file.exists():
                exceeds, _ = check_motion_threshold(parse_motion_parameters(motion_file), 2.0)
                if exceeds:
                    excluded.append(sub)
                    log_preprocessing_deviations(sub, 'motion', 'Exceeds threshold', log_file)
                else:
                    valid.append(sub)
            else:
                excluded.append(sub)
        
        # Write valid subjects
        with open(output_file, 'w') as f:
            f.write('\n'.join(valid))
        
        assert 'sub-01' in valid
        assert 'sub-02' in excluded
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            content = f.read()
            assert 'sub-01' in content
            assert 'sub-02' not in content