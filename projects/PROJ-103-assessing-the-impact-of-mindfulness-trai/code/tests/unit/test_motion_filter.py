"""
Unit tests for motion_filter module.
"""
import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.preprocessing.motion_filter import (
    MotionFilterError,
    load_motion_data,
    calculate_max_displacement,
    filter_subjects,
    write_exclusion_report,
    run_motion_filter
)

@pytest.fixture
def sample_motion_df():
    """Create a sample motion DataFrame."""
    data = {
        'subject_id': ['sub-01', 'sub-02', 'sub-03', 'sub-04'],
        'translation_x': [1.0, 4.0, 2.0, 0.5],
        'translation_y': [0.5, 1.0, 5.0, 0.2],
        'translation_z': [0.2, 0.3, 0.1, 3.5],
        'rotation_x': [0.1, 0.2, 0.1, 0.1],
        'rotation_y': [0.2, 3.5, 0.2, 0.2],
        'rotation_z': [0.1, 0.1, 0.1, 0.1]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_path():
    """Create a temporary CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_path = Path(f.name)
    yield temp_path
    if temp_path.exists():
        os.unlink(temp_path)

@pytest.fixture
def temp_json_path():
    """Create a temporary JSON file path."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    if temp_path.exists():
        os.unlink(temp_path)
    return temp_path

class TestLoadMotionData:
    def test_load_valid_csv(self, sample_motion_df, temp_csv_path):
        sample_motion_df.to_csv(temp_csv_path, index=False)
        df = load_motion_data(temp_csv_path)
        assert len(df) == 4
        assert 'subject_id' in df.columns

    def test_load_missing_file(self):
        with pytest.raises(MotionFilterError):
            load_motion_data(Path("/nonexistent/path.csv"))

    def test_load_invalid_columns(self, temp_csv_path):
        df = pd.DataFrame({'wrong_col': [1, 2, 3]})
        df.to_csv(temp_csv_path, index=False)
        with pytest.raises(MotionFilterError):
            load_motion_data(temp_csv_path)

class TestCalculateMaxDisplacement:
    def test_normal_values(self, sample_motion_df):
        row = sample_motion_df.iloc[0]
        max_trans, max_rot = calculate_max_displacement(row)
        assert max_trans == 1.0
        assert max_rot == 0.2

    def test_high_values(self, sample_motion_df):
        row = sample_motion_df.iloc[1]  # sub-02 with high motion
        max_trans, max_rot = calculate_max_displacement(row)
        assert max_trans == 4.0
        assert max_rot == 3.5

class TestFilterSubjects:
    def test_filter_correctly(self, sample_motion_df):
        included, excluded, details = filter_subjects(sample_motion_df)

        # sub-01: low motion -> included
        # sub-02: high trans (4.0) and high rot (3.5) -> excluded
        # sub-03: high trans (5.0) -> excluded
        # sub-04: high trans (3.5) -> excluded

        assert len(included) == 1
        assert included.iloc[0]['subject_id'] == 'sub-01'

        assert len(excluded) == 3
        excluded_ids = excluded['subject_id'].tolist()
        assert 'sub-02' in excluded_ids
        assert 'sub-03' in excluded_ids
        assert 'sub-04' in excluded_ids

        assert len(details) == 3

    def test_no_exclusions(self):
        data = {
            'subject_id': ['sub-01'],
            'translation_x': [1.0], 'translation_y': [1.0], 'translation_z': [1.0],
            'rotation_x': [0.1], 'rotation_y': [0.1], 'rotation_z': [0.1]
        }
        df = pd.DataFrame(data)
        included, excluded, details = filter_subjects(df)
        assert len(included) == 1
        assert len(excluded) == 0
        assert len(details) == 0

    def test_all_excluded(self):
        data = {
            'subject_id': ['sub-01'],
            'translation_x': [5.0], 'translation_y': [1.0], 'translation_z': [1.0],
            'rotation_x': [0.1], 'rotation_y': [0.1], 'rotation_z': [0.1]
        }
        df = pd.DataFrame(data)
        included, excluded, details = filter_subjects(df)
        assert len(included) == 0
        assert len(excluded) == 1
        assert len(details) == 1

class TestWriteExclusionReport:
    def test_write_report(self, temp_json_path):
        details = [
            {'subject_id': 'sub-01', 'max_translation_mm': 4.0, 'max_rotation_deg': 0.1, 'reason': 'Max translation 4.00mm > 3.0mm'}
        ]
        write_exclusion_report(details, temp_json_path)
        assert temp_json_path.exists()

        import json
        with open(temp_json_path, 'r') as f:
            report = json.load(f)

        assert report['total_excluded'] == 1
        assert report['exclusion_thresholds']['max_translation_mm'] == 3.0

class TestRunMotionFilter:
    def test_run_full_pipeline(self, sample_motion_df, temp_csv_path, temp_json_path):
        sample_motion_df.to_csv(temp_csv_path, index=False)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_csv = Path(tmpdir) / "filtered.csv"
            report_path = Path(tmpdir) / "report.json"

            included, excluded = run_motion_filter(temp_csv_path, output_csv, report_path)

            assert output_csv.exists()
            assert report_path.exists()
            assert len(included) == 1
            assert len(excluded) == 3