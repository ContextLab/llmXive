"""
Unit tests for motion_filter.py
"""

import os
import tempfile
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd

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
    """Create a sample DataFrame with motion parameters."""
    data = {
        'subject_id': ['sub-01', 'sub-02', 'sub-03', 'sub-04'],
        'translation_x': [1.0, 4.0, 2.0, 0.5],
        'translation_y': [1.0, 1.0, 2.0, 0.5],
        'translation_z': [1.0, 1.0, 2.0, 0.5],
        'rotation_x': [0.5, 0.5, 4.0, 0.1],
        'rotation_y': [0.5, 0.5, 0.5, 0.1],
        'rotation_z': [0.5, 0.5, 0.5, 0.1]
    }
    return pd.DataFrame(data)


@pytest.fixture
def temp_csv_path():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        path = Path(f.name)
    yield path
    if path.exists():
        path.unlink()


@pytest.fixture
def temp_json_path():
    """Create a temporary JSON file path for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        path = Path(f.name)
    yield path
    if path.exists():
        path.unlink()


class TestLoadMotionData:
    def test_load_valid_csv(self, sample_motion_df, temp_csv_path):
        """Test loading a valid CSV file."""
        sample_motion_df.to_csv(temp_csv_path, index=False)
        df = load_motion_data(temp_csv_path)
        assert len(df) == 4
        assert 'subject_id' in df.columns

    def test_load_missing_file(self):
        """Test that loading a missing file raises MotionFilterError."""
        with pytest.raises(MotionFilterError):
            load_motion_data(Path("nonexistent.csv"))

    def test_load_missing_columns(self, temp_csv_path):
        """Test that missing columns raise MotionFilterError."""
        df = pd.DataFrame({'subject_id': ['sub-01']})
        df.to_csv(temp_csv_path, index=False)
        with pytest.raises(MotionFilterError):
            load_motion_data(temp_csv_path)


class TestCalculateMaxDisplacement:
    def test_calculate_max(self, sample_motion_df):
        """Test calculation of max displacement."""
        row = sample_motion_df.iloc[1]  # sub-02: high translation
        translation_cols = ['translation_x', 'translation_y', 'translation_z']
        rotation_cols = ['rotation_x', 'rotation_y', 'rotation_z']

        max_trans, max_rot = calculate_max_displacement(row, translation_cols, rotation_cols)

        assert max_trans == 4.0  # max of [4.0, 1.0, 1.0]
        assert max_rot == 0.5    # max of [0.5, 0.5, 0.5]

    def test_calculate_high_rotation(self, sample_motion_df):
        """Test calculation with high rotation."""
        row = sample_motion_df.iloc[2]  # sub-03: high rotation
        translation_cols = ['translation_x', 'translation_y', 'translation_z']
        rotation_cols = ['rotation_x', 'rotation_y', 'rotation_z']

        max_trans, max_rot = calculate_max_displacement(row, translation_cols, rotation_cols)

        assert max_trans == 2.0
        assert max_rot == 4.0


class TestFilterSubjects:
    def test_filter_default_thresholds(self, sample_motion_df):
        """Test filtering with default thresholds (3mm, 3deg)."""
        included, excluded, filtered_df = filter_subjects(sample_motion_df)

        # sub-02: trans=4.0 > 3.0 -> excluded
        # sub-03: rot=4.0 > 3.0 -> excluded
        # sub-01, sub-04: within thresholds -> included
        assert len(included) == 2
        assert len(excluded) == 2
        assert 'sub-02' in excluded
        assert 'sub-03' in excluded
        assert 'sub-01' in included
        assert 'sub-04' in included

    def test_filter_custom_thresholds(self, sample_motion_df):
        """Test filtering with custom thresholds."""
        included, excluded, filtered_df = filter_subjects(
            sample_motion_df,
            translation_threshold_mm=5.0,
            rotation_threshold_deg=5.0
        )

        # All subjects should pass with higher thresholds
        assert len(included) == 4
        assert len(excluded) == 0

    def test_filter_strict_thresholds(self, sample_motion_df):
        """Test filtering with strict thresholds."""
        included, excluded, filtered_df = filter_subjects(
            sample_motion_df,
            translation_threshold_mm=1.5,
            rotation_threshold_deg=1.0
        )

        # sub-01: trans=1.0, rot=0.5 -> pass
        # sub-02: trans=4.0 -> fail
        # sub-03: rot=4.0 -> fail
        # sub-04: trans=0.5, rot=0.1 -> pass
        assert len(included) == 2
        assert len(excluded) == 2


class TestWriteExclusionReport:
    def test_write_report(self, temp_json_path):
        """Test writing an exclusion report."""
        excluded_ids = ['sub-02', 'sub-03']
        metadata = {"translation_threshold_mm": 3.0, "rotation_threshold_deg": 3.0}

        write_exclusion_report(excluded_ids, temp_json_path, metadata)

        assert temp_json_path.exists()
        with open(temp_json_path, 'r') as f:
            report = json.load(f)

        assert report['total_excluded'] == 2
        assert set(report['excluded_subject_ids']) == set(excluded_ids)
        assert report['exclusion_criteria']['max_translation_mm'] == 3.0

    def test_write_report_no_metadata(self, temp_json_path):
        """Test writing report without metadata."""
        excluded_ids = ['sub-01']
        write_exclusion_report(excluded_ids, temp_json_path, None)

        with open(temp_json_path, 'r') as f:
            report = json.load(f)

        assert report['exclusion_criteria']['max_translation_mm'] == 3.0  # default


class TestRunMotionFilter:
    def test_run_full_pipeline(self, sample_motion_df, temp_csv_path, temp_json_path, tmp_path):
        """Test the full motion filtering pipeline."""
        output_csv = tmp_path / "filtered.csv"
        output_report = tmp_path / "report.json"

        sample_motion_df.to_csv(temp_csv_path, index=False)

        result = run_motion_filter(
            input_motion_csv=temp_csv_path,
            output_filtered_csv=output_csv,
            output_report_json=output_report,
            translation_threshold_mm=3.0,
            rotation_threshold_deg=3.0
        )

        assert result['total_subjects'] == 4
        assert result['included_count'] == 2
        assert result['excluded_count'] == 2
        assert output_csv.exists()
        assert output_report.exists()

        # Verify filtered CSV content
        filtered_df = pd.read_csv(output_csv)
        assert len(filtered_df) == 2
        assert 'sub-02' not in filtered_df['subject_id'].values
        assert 'sub-03' not in filtered_df['subject_id'].values

    def test_run_all_excluded(self, tmp_path):
        """Test pipeline when all subjects are excluded."""
        data = {
            'subject_id': ['sub-01'],
            'translation_x': [10.0],
            'translation_y': [1.0],
            'translation_z': [1.0],
            'rotation_x': [1.0],
            'rotation_y': [1.0],
            'rotation_z': [1.0]
        }
        input_df = pd.DataFrame(data)

        input_csv = tmp_path / "input.csv"
        output_csv = tmp_path / "output.csv"
        output_report = tmp_path / "report.json"

        input_df.to_csv(input_csv, index=False)

        result = run_motion_filter(
            input_motion_csv=input_csv,
            output_filtered_csv=output_csv,
            output_report_json=output_report,
            translation_threshold_mm=3.0,
            rotation_threshold_deg=3.0
        )

        assert result['included_count'] == 0
        assert result['excluded_count'] == 1
        assert output_csv.exists()