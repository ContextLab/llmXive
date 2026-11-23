import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from code.data.behavioral_extraction import (
    load_metadata,
    extract_behavioral_metrics,
    save_behavioral_metrics,
)


class TestLoadMetadata:
    def test_loads_csv_correctly(self):
        """Test that metadata is loaded correctly from CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_path = Path(tmpdir) / "metadata.csv"
            data = {
                'subject_id': ['sub-001', 'sub-002', 'sub-003'],
                'pre_motor_score': [10.5, 12.0, 11.2],
                'post_motor_score': [15.0, 14.5, 16.0],
                'age': [25, 30, 28],
                'sex': ['M', 'F', 'M']
            }
            df = pd.DataFrame(data)
            df.to_csv(metadata_path, index=False)

            result = load_metadata(str(metadata_path))

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3
            assert 'subject_id' in result.columns
            assert 'pre_motor_score' in result.columns

    def test_handles_missing_file(self):
        """Test behavior when file is missing."""
        with pytest.raises(FileNotFoundError):
            load_metadata("/nonexistent/path/metadata.csv")

    def test_handles_empty_file(self):
        """Test behavior with empty file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_path = Path(tmpdir) / "metadata.csv"
            df = pd.DataFrame()
            df.to_csv(metadata_path, index=False)

            with pytest.raises((KeyError, ValueError)):
                load_metadata(str(metadata_path))

    def test_requires_required_columns(self):
        """Test that required columns are enforced."""
        with tempfile.TemporaryDirectory() as tmpdir:
            metadata_path = Path(tmpdir) / "metadata.csv"
            data = {
                'subject_id': ['sub-001'],
                'other_column': [10]
            }
            df = pd.DataFrame(data)
            df.to_csv(metadata_path, index=False)

            with pytest.raises(KeyError):
                load_metadata(str(metadata_path))


class TestExtractBehavioralMetrics:
    def test_calculates_improvement_score(self):
        """Test that improvement score is calculated correctly."""
        data = {
            'subject_id': ['sub-001', 'sub-002'],
            'pre_motor_score': [10.0, 15.0],
            'post_motor_score': [15.0, 14.0],
            'age': [25, 30],
            'sex': ['M', 'F']
        }
        df = pd.DataFrame(data)

        result = extract_behavioral_metrics(df)

        assert 'improvement_score' in result.columns
        # sub-001: 15.0 - 10.0 = 5.0
        # sub-002: 14.0 - 15.0 = -1.0
        assert result.iloc[0]['improvement_score'] == 5.0
        assert result.iloc[1]['improvement_score'] == -1.0

    def test_preserves_all_columns(self):
        """Test that all original columns are preserved."""
        data = {
            'subject_id': ['sub-001'],
            'pre_motor_score': [10.0],
            'post_motor_score': [15.0],
            'age': [25],
            'sex': ['M']
        }
        df = pd.DataFrame(data)

        result = extract_behavioral_metrics(df)

        expected_columns = ['subject_id', 'pre_motor_score', 'post_motor_score',
                            'age', 'sex', 'improvement_score']
        assert list(result.columns) == expected_columns

    def test_handles_missing_values(self):
        """Test behavior with missing values in scores."""
        data = {
            'subject_id': ['sub-001', 'sub-002'],
            'pre_motor_score': [10.0, np.nan],
            'post_motor_score': [15.0, 14.0],
            'age': [25, 30],
            'sex': ['M', 'F']
        }
        df = pd.DataFrame(data)

        result = extract_behavioral_metrics(df)

        # Should handle NaN gracefully, possibly resulting in NaN improvement
        assert len(result) == 2
        assert pd.isna(result.iloc[1]['improvement_score'])


class TestSaveBehavioralMetrics:
    def test_saves_correctly(self):
        """Test that metrics are saved correctly to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subject_scores.csv"
            data = {
                'subject_id': ['sub-001'],
                'pre_motor_score': [10.0],
                'post_motor_score': [15.0],
                'age': [25],
                'sex': ['M'],
                'improvement_score': [5.0]
            }
            df = pd.DataFrame(data)

            save_behavioral_metrics(df, str(output_path))

            assert output_path.exists()
            saved_df = pd.read_csv(output_path)
            assert len(saved_df) == 1
            assert saved_df.iloc[0]['improvement_score'] == 5.0

    def test_creates_directory_if_not_exists(self):
        """Test that the function creates the output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "nested" / "output" / "subject_scores.csv"
            data = {
                'subject_id': ['sub-001'],
                'pre_motor_score': [10.0],
                'post_motor_score': [15.0],
                'age': [25],
                'sex': ['M'],
                'improvement_score': [5.0]
            }
            df = pd.DataFrame(data)

            save_behavioral_metrics(df, str(nested_path))

            assert nested_path.exists()

    def test_handles_empty_dataframe(self):
        """Test behavior with empty DataFrame."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subject_scores.csv"
            df = pd.DataFrame()

            # Should handle empty DataFrame, possibly creating empty file
            save_behavioral_metrics(df, str(output_path))
            assert output_path.exists()
