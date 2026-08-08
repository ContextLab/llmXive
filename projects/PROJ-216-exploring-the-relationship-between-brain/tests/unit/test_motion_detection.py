import os
import sys
import csv
import json
import tempfile
from pathlib import Path
import pytest

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from motion_detection import (
    load_motion_metrics,
    get_valid_subjects,
    detect_motion_artifacts,
    write_motion_exclusion_log,
    TRANSLATION_THRESHOLD_MM,
    ROTATION_THRESHOLD_MM
)

class TestMotionDetection:
    """Unit tests for motion artifact detection logic."""

    def test_load_motion_metrics_found(self, tmp_path):
        """Test loading motion metrics when file exists."""
        # Create test motion metrics file
        subject_id = "sub-001"
        motion_file = tmp_path / f"{subject_id}_motion_metrics.json"
        test_data = {
            "translation_mm": 1.5,
            "rotation_mm": 0.8
        }
        with open(motion_file, 'w') as f:
            json.dump(test_data, f)
        
        result = load_motion_metrics(subject_id, tmp_path)
        
        assert result is not None
        assert result['translation_mm'] == 1.5
        assert result['rotation_mm'] == 0.8

    def test_load_motion_metrics_not_found(self, tmp_path):
        """Test loading motion metrics when file does not exist."""
        subject_id = "sub-001"
        result = load_motion_metrics(subject_id, tmp_path)
        
        assert result is None

    def test_get_valid_subjects(self, tmp_path):
        """Test loading valid subjects from JSON."""
        valid_file = tmp_path / "valid_subjects.json"
        test_data = {
            "subjects": [
                {"id": "sub-001", "score": 2.5},
                {"id": "sub-002", "score": 3.1}
            ],
            "count": 2
        }
        with open(valid_file, 'w') as f:
            json.dump(test_data, f)
        
        subjects = get_valid_subjects(valid_file)
        
        assert len(subjects) == 2
        assert "sub-001" in subjects
        assert "sub-002" in subjects

    def test_detect_motion_artifacts_exclusion_logic(self, tmp_path):
        """Test that motion artifacts are correctly detected based on thresholds."""
        # Create test motion metrics files
        subjects_data = {
            "sub-001": {"translation_mm": 1.0, "rotation_mm": 0.5},  # Pass
            "sub-002": {"translation_mm": 4.0, "rotation_mm": 0.5},  # Fail (translation > 3)
            "sub-003": {"translation_mm": 1.0, "rotation_mm": 3.0},  # Fail (rotation > 2)
            "sub-004": {"translation_mm": 2.0, "rotation_mm": 1.5},  # Pass (at boundary)
            "sub-005": {"translation_mm": 3.1, "rotation_mm": 2.1}   # Fail (both over)
        }
        
        for subj_id, metrics in subjects_data.items():
            motion_file = tmp_path / f"{subj_id}_motion_metrics.json"
            with open(motion_file, 'w') as f:
                json.dump(metrics, f)
        
        subject_list = list(subjects_data.keys())
        output_file = tmp_path / "motion_exclusion_log.csv"
        
        results = detect_motion_artifacts(subject_list, tmp_path, output_file)
        
        # Verify results
        result_dict = {r['subject_id']: r for r in results}
        
        # sub-001: Pass
        assert result_dict['sub-001']['excluded'] == False
        assert result_dict['sub-001']['translation_mm'] == 1.0
        assert result_dict['sub-001']['rotation_mm'] == 0.5
        
        # sub-002: Fail (translation)
        assert result_dict['sub-002']['excluded'] == True
        assert result_dict['sub-002']['translation_mm'] == 4.0
        
        # sub-003: Fail (rotation)
        assert result_dict['sub-003']['excluded'] == True
        assert result_dict['sub-003']['rotation_mm'] == 3.0
        
        # sub-004: Pass (at boundary, not exceeding)
        assert result_dict['sub-004']['excluded'] == False
        
        # sub-005: Fail (both)
        assert result_dict['sub-005']['excluded'] == True

    def test_write_motion_exclusion_log_csv_format(self, tmp_path):
        """Test that the output CSV has correct columns and format."""
        test_results = [
            {
                'subject_id': 'sub-001',
                'translation_mm': 1.5,
                'rotation_mm': 0.8,
                'excluded': False
            },
            {
                'subject_id': 'sub-002',
                'translation_mm': 4.0,
                'rotation_mm': 0.5,
                'excluded': True
            }
        ]
        
        output_file = tmp_path / "motion_exclusion_log.csv"
        write_motion_exclusion_log(test_results, output_file)
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert 'subject_id' in rows[0]
        assert 'translation_mm' in rows[0]
        assert 'rotation_mm' in rows[0]
        assert 'excluded' in rows[0]
        
        # Verify boolean conversion in CSV
        assert rows[0]['excluded'] == 'False'
        assert rows[1]['excluded'] == 'True'

    def test_missing_motion_metrics_handling(self, tmp_path):
        """Test handling of subjects with missing motion metrics."""
        # Create only one motion metrics file
        subject_id = "sub-001"
        motion_file = tmp_path / f"{subject_id}_motion_metrics.json"
        with open(motion_file, 'w') as f:
            json.dump({"translation_mm": 1.0, "rotation_mm": 0.5}, f)
        
        # Request metrics for two subjects, one missing
        results = detect_motion_artifacts(
            ["sub-001", "sub-002"],
            tmp_path,
            tmp_path / "output.csv"
        )
        
        assert len(results) == 2
        
        # sub-001 should have metrics
        sub001_result = next(r for r in results if r['subject_id'] == 'sub-001')
        assert sub001_result['excluded'] == False
        
        # sub-002 should be excluded due to missing data
        sub002_result = next(r for r in results if r['subject_id'] == 'sub-002')
        assert sub002_result['excluded'] == True
        assert sub002_result['translation_mm'] is None
        assert sub002_result['rotation_mm'] is None
