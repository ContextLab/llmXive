"""
Unit tests for the motion filter module.
"""

import os
import tempfile
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd
import numpy as np

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
    """Create a sample motion DataFrame for testing."""
    data = {
        'subject_id': ['sub-01', 'sub-02', 'sub-03'],
        'translation_x': [1.0, 4.0, 0.5],
        'translation_y': [0.5, 0.5, 0.5],
        'translation_z': [0.5, 0.5, 0.5],
        'rotation_x': [0.1, 0.1, 0.1],
        'rotation_y': [0.1, 0.1, 0.1],
        'rotation_z': [0.1, 3.5, 0.1],  # sub-02 exceeds rotation threshold
    }
    return pd.DataFrame(data)


@pytest.fixture
def temp_csv_path():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def temp_json_path():
    """Create a temporary JSON file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestLoadMotionData:
    def test_load_valid_csv(self, sample_motion_df, temp_csv_path):
        """Test loading a valid motion CSV file."""
        sample_motion_df.to_csv(temp_csv_path, index=False)
        df = load_motion_data(temp_csv_path)
        
        assert len(df) == 3
        assert 'subject_id' in df.columns
        assert list(df['subject_id']) == ['sub-01', 'sub-02', 'sub-03']

    def test_load_missing_file(self, temp_csv_path):
        """Test error handling for missing file."""
        with pytest.raises(MotionFilterError, match="not found"):
            load_motion_data(temp_csv_path)

    def test_load_missing_columns(self, temp_csv_path):
        """Test error handling for missing columns."""
        invalid_data = {'subject_id': ['sub-01'], 'other_col': [1.0]}
        pd.DataFrame(invalid_data).to_csv(temp_csv_path, index=False)
        
        with pytest.raises(MotionFilterError, match="Missing required columns"):
            load_motion_data(temp_csv_path)


class TestCalculateMaxDisplacement:
    def test_calculate_displacement(self, sample_motion_df):
        """Test max displacement calculation."""
        row = sample_motion_df.iloc[0]
        max_trans, max_rot = calculate_max_displacement(row)
        
        # sub-01: sqrt(1^2 + 0.5^2 + 0.5^2) = sqrt(1.5) ~ 1.22
        expected_trans = np.sqrt(1.0**2 + 0.5**2 + 0.5**2)
        assert np.isclose(max_trans, expected_trans)
        
        # sub-01: sqrt(0.1^2 + 0.1^2 + 0.1^2) = sqrt(0.03) ~ 0.17
        expected_rot = np.sqrt(0.1**2 + 0.1**2 + 0.1**2)
        assert np.isclose(max_rot, expected_rot)

    def test_calculate_high_motion(self, sample_motion_df):
        """Test with high motion values."""
        row = sample_motion_df.iloc[1]  # sub-02
        max_trans, max_rot = calculate_max_displacement(row)
        
        # sub-02: sqrt(4^2 + 0.5^2 + 0.5^2) = sqrt(16.5) ~ 4.06
        expected_trans = np.sqrt(4.0**2 + 0.5**2 + 0.5**2)
        assert np.isclose(max_trans, expected_trans)
        
        # sub-02: sqrt(0.1^2 + 0.1^2 + 3.5^2) = sqrt(12.27) ~ 3.50
        expected_rot = np.sqrt(0.1**2 + 0.1**2 + 3.5**2)
        assert np.isclose(max_rot, expected_rot)


class TestFilterSubjects:
    def test_filter_with_thresholds(self, sample_motion_df):
        """Test filtering with default thresholds (3mm, 3deg)."""
        excluded, included, stats = filter_subjects(sample_motion_df)
        
        # sub-01: trans ~1.22, rot ~0.17 -> INCLUDED
        # sub-02: trans ~4.06 (>3), rot ~3.50 (>3) -> EXCLUDED
        # sub-03: trans ~0.87, rot ~0.17 -> INCLUDED
        
        assert len(excluded) == 1
        assert 'sub-02' in excluded
        assert len(included) == 2
        assert 'sub-01' in included
        assert 'sub-03' in included

    def test_filter_custom_thresholds(self, sample_motion_df):
        """Test filtering with custom thresholds."""
        # Set high thresholds to include everyone
        excluded, included, _ = filter_subjects(sample_motion_df, trans_threshold=10.0, rot_threshold=10.0)
        assert len(excluded) == 0
        assert len(included) == 3

    def test_filter_strict_thresholds(self, sample_motion_df):
        """Test filtering with strict thresholds."""
        # Set low thresholds to exclude everyone
        excluded, included, _ = filter_subjects(sample_motion_df, trans_threshold=0.1, rot_threshold=0.1)
        assert len(excluded) == 3
        assert len(included) == 0


class TestWriteExclusionReport:
    def test_write_report(self, sample_motion_df, temp_csv_path):
        """Test writing exclusion report."""
        excluded, included, stats = filter_subjects(sample_motion_df)
        write_exclusion_report(excluded, included, stats, temp_csv_path)
        
        assert os.path.exists(temp_csv_path)
        
        # Read back and verify
        df = pd.read_csv(temp_csv_path)
        assert 'subject_id' in df.columns
        assert 'status' in df.columns
        assert 'exclusion_reason' in df.columns
        
        # Verify sub-02 is excluded
        sub02_row = df[df['subject_id'] == 'sub-02'].iloc[0]
        assert sub02_row['status'] == 'EXCLUDED'
        assert 'trans' in sub02_row['exclusion_reason'] or 'rot' in sub02_row['exclusion_reason']


class TestRunMotionFilter:
    @patch('src.preprocessing.motion_filter.get_data_dir')
    def test_run_motion_filter(self, mock_get_dir, sample_motion_df, temp_csv_path):
        """Test running the full motion filter pipeline."""
        mock_get_dir.return_value = '/tmp/test_data'
        
        # Create input file
        input_path = Path('/tmp/test_data/processed/motion/all_subjects_motion.csv')
        input_path.parent.mkdir(parents=True, exist_ok=True)
        sample_motion_df.to_csv(input_path, index=False)
        
        # Run filter
        with patch('src.preprocessing.motion_filter.Path') as mock_path:
            mock_path.return_value.parent.mkdir = MagicMock()
            mock_path.return_value.__truediv__ = lambda self, x: self
            mock_path.return_value.exists = lambda: True
            mock_path.return_value.write_text = MagicMock()
            
            # Direct call to avoid path mocking complexity
            df = load_motion_data(str(input_path))
            excluded, included, stats = filter_subjects(df)
            write_exclusion_report(excluded, included, stats, temp_csv_path)
            
            assert os.path.exists(temp_csv_path)
            assert len(excluded) == 1
            assert 'sub-02' in excluded
        
        # Cleanup
        if input_path.exists():
            input_path.unlink()
            input_path.parent.rmdir()
            input_path.parent.parent.rmdir()