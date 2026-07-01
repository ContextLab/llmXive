"""
Unit tests for the motion filter module.
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
    """Create a sample DataFrame with motion parameters."""
    data = {
        'subject_id': ['sub-01', 'sub-02', 'sub-03', 'sub-04'],
        'translation_x': [1.0, 5.0, 2.0, 0.5],
        'translation_y': [1.0, 2.0, 2.0, 0.5],
        'translation_z': [1.0, 2.0, 2.0, 0.5],
        'rotation_x': [1.0, 2.0, 4.0, 0.5],
        'rotation_y': [1.0, 2.0, 2.0, 0.5],
        'rotation_z': [1.0, 2.0, 2.0, 0.5],
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv_path(sample_motion_df):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_motion_df.to_csv(f, index=False)
        path = Path(f.name)
    yield path
    os.unlink(path)

class TestLoadMotionData:
    def test_load_success(self, temp_csv_path, sample_motion_df):
        df = load_motion_data(temp_csv_path)
        pd.testing.assert_frame_equal(df, sample_motion_df)

    def test_load_file_not_found(self):
        with pytest.raises(MotionFilterError, match="not found"):
            load_motion_data(Path("/nonexistent/path.csv"))

    def test_load_missing_columns(self, temp_csv_path):
        # Create a file with missing columns
        bad_data = pd.DataFrame({'subject_id': ['sub-01']})
        with open(temp_csv_path, 'w') as f:
            bad_data.to_csv(f, index=False)
        
        with pytest.raises(MotionFilterError, match="Missing required columns"):
            load_motion_data(temp_csv_path)

class TestCalculateMaxDisplacement:
    def test_max_translation(self):
        row = pd.Series({
            'translation_x': 1.0, 'translation_y': 5.0, 'translation_z': 2.0,
            'rotation_x': 1.0, 'rotation_y': 1.0, 'rotation_z': 1.0
        })
        max_trans, max_rot = calculate_max_displacement(row)
        assert max_trans == 5.0
        assert max_rot == 1.0

    def test_max_rotation(self):
        row = pd.Series({
            'translation_x': 1.0, 'translation_y': 1.0, 'translation_z': 1.0,
            'rotation_x': 4.0, 'rotation_y': 2.0, 'rotation_z': 1.0
        })
        max_trans, max_rot = calculate_max_displacement(row)
        assert max_trans == 1.0
        assert max_rot == 4.0

    def test_negative_values(self):
        row = pd.Series({
            'translation_x': -5.0, 'translation_y': 1.0, 'translation_z': 1.0,
            'rotation_x': 1.0, 'rotation_y': -3.0, 'rotation_z': 1.0
        })
        max_trans, max_rot = calculate_max_displacement(row)
        assert max_trans == 5.0
        assert max_rot == 3.0

class TestFilterSubjects:
    def test_filter_within_limits(self, sample_motion_df):
        # sub-01: max_trans=1, max_rot=1 -> Included
        included, excluded, log = filter_subjects(
            sample_motion_df, 
            trans_threshold=3.0, 
            rot_threshold=3.0
        )
        assert len(included) == 3 # sub-01, sub-03, sub-04
        assert len(excluded) == 1 # sub-02
        assert excluded.iloc[0]['subject_id'] == 'sub-02'

    def test_filter_excluded_translation(self, sample_motion_df):
        # sub-02 has trans_x=5.0
        included, excluded, log = filter_subjects(
            sample_motion_df, 
            trans_threshold=3.0, 
            rot_threshold=3.0
        )
        assert 'sub-02' in excluded['subject_id'].values

    def test_filter_excluded_rotation(self, sample_motion_df):
        # sub-03 has rot_x=4.0
        included, excluded, log = filter_subjects(
            sample_motion_df, 
            trans_threshold=3.0, 
            rot_threshold=3.0
        )
        assert 'sub-03' in excluded['subject_id'].values

    def test_filter_empty_excluded(self):
        data = {
            'subject_id': ['sub-01'],
            'translation_x': [1.0], 'translation_y': [1.0], 'translation_z': [1.0],
            'rotation_x': [1.0], 'rotation_y': [1.0], 'rotation_z': [1.0],
        }
        df = pd.DataFrame(data)
        included, excluded, log = filter_subjects(df, trans_threshold=3.0, rot_threshold=3.0)
        assert len(included) == 1
        assert len(excluded) == 0
        assert log[0]['status'] == 'INCLUDED'

class TestWriteExclusionReport:
    def test_write_report(self):
        log = [
            {"subject_id": "sub-01", "max_translation_mm": 1.0, "max_rotation_deg": 1.0, "status": "INCLUDED", "reason": "Within limits"},
            {"subject_id": "sub-02", "max_translation_mm": 5.0, "max_rotation_deg": 2.0, "status": "EXCLUDED", "reason": "Trans 5.00mm > 3.0mm"}
        ]
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            path = Path(f.name)
        
        write_exclusion_report(log, path)
        
        assert path.exists()
        df = pd.read_csv(path)
        assert len(df) == 2
        assert df.iloc[0]['subject_id'] == 'sub-01'
        assert df.iloc[1]['subject_id'] == 'sub-02'
        
        os.unlink(path)

class TestRunMotionFilter:
    @patch('src.preprocessing.motion_filter.get_data_dir')
    def test_run_full_pipeline(self, mock_get_data_dir, sample_motion_df, temp_csv_path):
        mock_get_data_dir.return_value = tempfile.gettempdir()
        
        # Create output paths
        out_inc = Path(tempfile.gettempdir()) / "test_included.csv"
        out_exc = Path(tempfile.gettempdir()) / "test_excluded.csv"
        out_rep = Path(tempfile.gettempdir()) / "test_report.csv"
        
        try:
            result = run_motion_filter(
                input_csv_path=temp_csv_path,
                output_included_path=out_inc,
                output_excluded_path=out_exc,
                output_report_path=out_rep,
                trans_threshold=3.0,
                rot_threshold=3.0
            )
            
            assert result['total_subjects'] == 4
            assert result['included_count'] == 2 # sub-01, sub-04
            assert result['excluded_count'] == 2 # sub-02, sub-03
            
            assert out_inc.exists()
            assert out_exc.exists()
            assert out_rep.exists()
            
            df_inc = pd.read_csv(out_inc)
            assert 'sub-01' in df_inc['subject_id'].values
            assert 'sub-04' in df_inc['subject_id'].values
            
        finally:
            for p in [out_inc, out_exc, out_rep]:
                if p.exists():
                    os.unlink(p)