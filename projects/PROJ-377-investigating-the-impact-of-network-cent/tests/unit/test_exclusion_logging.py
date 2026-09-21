import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os

from code.data.exclusion_logging import (
    load_retention_metrics,
    load_behavioral_data,
    determine_exclusions,
    save_exclusion_log,
)


class TestLoadRetentionMetrics:
    def test_loads_json_correctly(self):
        """Test that retention metrics are loaded correctly from JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = Path(tmpdir) / "retention_metrics.json"
            metrics = {
                'retention_rate': 0.95,
                'total_subjects': 100,
                'retained_subjects': 95,
                'excluded_subjects': 5
            }
            with open(metrics_path, 'w') as f:
                import json
                json.dump(metrics, f)

            result = load_retention_metrics(str(metrics_path))

            assert isinstance(result, dict)
            assert result['retention_rate'] == 0.95
            assert result['total_subjects'] == 100

    def test_handles_missing_file(self):
        """Test behavior when file is missing."""
        with pytest.raises(FileNotFoundError):
            load_retention_metrics("/nonexistent/path/retention_metrics.json")

    def test_handles_invalid_json(self):
        """Test behavior with invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics_path = Path(tmpdir) / "retention_metrics.json"
            with open(metrics_path, 'w') as f:
                f.write("invalid json {")

            with pytest.raises((json.JSONDecodeError, ValueError)):
                load_retention_metrics(str(metrics_path))


class TestLoadBehavioralData:
    def test_loads_correctly(self):
        """Test that behavioral data is loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "subject_scores.csv"
            data = {
                'subject_id': ['sub-001', 'sub-002', 'sub-003'],
                'pre_motor_score': [10.0, 12.0, 11.0],
                'post_motor_score': [15.0, 14.0, 16.0],
                'age': [25, 30, 28],
                'sex': ['M', 'F', 'M'],
                'improvement_score': [5.0, 2.0, 5.0]
            }
            df = pd.DataFrame(data)
            df.to_csv(data_path, index=False)

            result = load_behavioral_data(str(data_path))

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3

    def test_handles_missing_file(self):
        """Test behavior when file is missing."""
        with pytest.raises(FileNotFoundError):
            load_behavioral_data("/nonexistent/path/subject_scores.csv")


class TestDetermineExclusions:
    def test_identifies_missing_behavioral_data(self):
        """Test that missing behavioral data is identified."""
        retention_metrics = {
            'total_subjects': 100,
            'retained_subjects': 90
        }
        behavioral_data = pd.DataFrame({
            'subject_id': [f'sub-{i:03d}' for i in range(1, 91)],
            'pre_motor_score': [10.0] * 85 + [np.nan] * 5,  # 5 missing
            'post_motor_score': [15.0] * 90
        })

        exclusions, retention_rate = determine_exclusions(retention_metrics, behavioral_data)

        assert len(exclusions) > 0
        # Should identify subjects with missing data
        assert any('missing' in exc['reason'].lower() for exc in exclusions)

    def test_identifies_motion_artifacts(self):
        """Test that motion artifacts are identified when FD threshold is exceeded."""
        retention_metrics = {
            'total_subjects': 100,
            'retained_subjects': 95
        }
        behavioral_data = pd.DataFrame({
            'subject_id': [f'sub-{i:03d}' for i in range(1, 96)],
            'pre_motor_score': [10.0] * 95,
            'post_motor_score': [15.0] * 95,
            'mean_fd': [0.1] * 90 + [0.5] * 5  # 5 with high FD
        })

        exclusions, retention_rate = determine_exclusions(retention_metrics, behavioral_data, fd_threshold=0.3)

        # Should identify subjects with high FD
        assert any('motion' in exc['reason'].lower() or 'fd' in exc['reason'].lower() for exc in exclusions)

    def test_calculates_retention_rate(self):
        """Test that retention rate is calculated correctly."""
        retention_metrics = {
            'total_subjects': 100,
            'retained_subjects': 90
        }
        behavioral_data = pd.DataFrame({
            'subject_id': [f'sub-{i:03d}' for i in range(1, 91)],
            'pre_motor_score': [10.0] * 90,
            'post_motor_score': [15.0] * 90
        })

        exclusions, retention_rate = determine_exclusions(retention_metrics, behavioral_data)

        assert 0 <= retention_rate <= 1
        assert retention_rate <= 1.0


class TestSaveExclusionLog:
    def test_saves_correctly(self):
        """Test that exclusion log is saved correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "exclusion_log.csv"
            exclusions = [
                {'subject_id': 'sub-001', 'reason': 'Missing pre_motor_score'},
                {'subject_id': 'sub-002', 'reason': 'High motion artifacts'},
                {'subject_id': 'sub-003', 'reason': 'Missing post_motor_score'}
            ]

            save_exclusion_log(exclusions, str(log_path))

            assert log_path.exists()
            saved_df = pd.read_csv(log_path)
            assert len(saved_df) == 3
            assert 'subject_id' in saved_df.columns
            assert 'reason' in saved_df.columns

    def test_handles_empty_exclusions(self):
        """Test behavior with empty exclusions list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "exclusion_log.csv"
            exclusions = []

            save_exclusion_log(exclusions, str(log_path))

            assert log_path.exists()
            saved_df = pd.read_csv(log_path)
            assert len(saved_df) == 0

    def test_creates_directory_if_not_exists(self):
        """Test that the function creates the output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "nested" / "output" / "exclusion_log.csv"
            exclusions = [
                {'subject_id': 'sub-001', 'reason': 'Missing data'}
            ]

            save_exclusion_log(exclusions, str(nested_path))

            assert nested_path.exists()
