import pytest
import os
import csv
import tempfile
from pathlib import Path

from data.loader import Participant, validate_and_filter_subjects, filter_by_motion

def test_full_exclusion_logging_flow():
    """
    Integration test ensuring the full flow of exclusion logging works correctly
    across multiple exclusion reasons in a single run.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup mock config
        import config
        original_data_path = config.get_config().DATA_PATH
        config.get_config().DATA_PATH = tmpdir
        
        # Prepare subjects with various exclusion conditions
        subjects = [
            # Valid subject
            Participant(subject_id="valid_01", fmri_path="/fake.nii", behavioral_data={"CAQ": 100}),
            # Missing scan
            Participant(subject_id="no_scan_01", fmri_path=None, behavioral_data={"CAQ": 100}),
            # Missing score
            Participant(subject_id="no_score_01", fmri_path="/fake.nii", behavioral_data={}),
            # High motion
            Participant(subject_id="high_motion_01", fmri_path="/fake.nii", behavioral_data={"CAQ": 100}, motion_metrics={'mean_fd': 0.8, 'high_vol_pct': 0.1}),
            # Valid subject 2
            Participant(subject_id="valid_02", fmri_path="/fake.nii", behavioral_data={"CAQ": 120}),
        ]
        
        # Mock file existence for valid paths
        with patch('os.path.exists', return_value=True):
            # First pass: validate and filter
            filtered_1 = validate_and_filter_subjects(subjects)
            
            # Second pass: filter by motion
            final_subjects = filter_by_motion(filtered_1)
        
        # Assertions on results
        assert len(final_subjects) == 2
        assert {s.subject_id for s in final_subjects} == {"valid_01", "valid_02"}
        
        # Assertions on log file
        log_path = os.path.join(tmpdir, "data_exclusion_log.txt")
        assert os.path.exists(log_path), "Log file not created"
        
        with open(log_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # We expect 3 exclusions: no_scan (skipped, not logged as exclusion), no_score, high_motion
        # Note: no_scan is skipped via 'continue' before log_exclusion is called in validate_and_filter_subjects
        # So we expect 2 logged exclusions: MISSING_SCORE and HIGH_MOTION
        assert len(rows) == 2
        
        reasons = [r['reason'] for r in rows]
        assert 'MISSING_SCORE' in reasons
        assert 'HIGH_MOTION' in reasons
        
        # Verify specific subjects
        logged_ids = [r['subject_id'] for r in rows]
        assert 'no_score_01' in logged_ids
        assert 'high_motion_01' in logged_ids
        
        # Restore config
        config.get_config().DATA_PATH = original_data_path
