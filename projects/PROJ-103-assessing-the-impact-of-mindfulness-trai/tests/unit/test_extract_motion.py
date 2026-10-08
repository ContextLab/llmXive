"""
Unit tests for motion parameter extraction from fMRIPrep output.
"""

import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.preprocessing.extract_motion import (
    MotionExtractionError,
    find_fmriprep_confounds,
    extract_subject_id_from_path,
    extract_motion_parameters,
    extract_all_motion_parameters,
    write_motion_csv,
    run_motion_extraction
)


@pytest.fixture
def temp_confounds_dir():
    """Create a temporary directory with mock fMRIPrep confounds files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create directory structure
        sub_dir = tmpdir_path / "processed" / "ds000001" / "sub-001" / "func"
        sub_dir.mkdir(parents=True)

        # Create a mock confounds TSV file
        confounds_data = """
        trans_x\ttrans_y\ttrans_z\trot_x\trot_y\trot_z\tframewise_displacement
        0.1\t0.2\t0.3\t0.01\t0.02\t0.03\t0.1
        0.15\t0.25\t0.35\t0.015\t0.025\t0.035\t0.15
        0.2\t0.3\t0.4\t0.02\t0.03\t0.04\t0.2
        """.strip()

        confounds_file = sub_dir / "sub-001_task-rest_desc-confounds_regressors.tsv"
        confounds_file.write_text(confounds_data)

        # Create another subject
        sub2_dir = tmpdir_path / "processed" / "ds000001" / "sub-002" / "func"
        sub2_dir.mkdir(parents=True)

        confounds_data2 = """
        trans_x\ttrans_y\ttrans_z\trot_x\trot_y\trot_z\tframewise_displacement
        0.5\t0.6\t0.7\t0.05\t0.06\t0.07\t0.5
        0.55\t0.65\t0.75\t0.055\t0.065\t0.075\t0.55
        """.strip()

        confounds_file2 = sub2_dir / "sub-002_task-rest_desc-confounds_regressors.tsv"
        confounds_file2.write_text(confounds_data2)

        yield tmpdir_path


@pytest.fixture
def mock_env_data_dir(temp_confounds_dir):
    """Mock the environment data directory."""
    with patch('src.preprocessing.extract_motion.get_data_dir', return_value=str(temp_confounds_dir)):
        yield temp_confounds_dir


class TestExtractSubjectId:
    def test_extract_from_path_sub_folder(self):
        """Test extraction when sub-<id> is in path."""
        path = Path("/data/processed/sub-001/func/confounds.tsv")
        assert extract_subject_id_from_path(path) == "sub-001"

    def test_extract_from_filename_prefix(self):
        """Test extraction from filename prefix."""
        path = Path("/data/sub-002_task-rest_confounds.tsv")
        assert extract_subject_id_from_path(path) == "sub-002"

    def test_extract_complex_path(self):
        """Test extraction from complex nested path."""
        path = Path("/data/processed/ds001/sub-003/func/sub-003_task-rest_desc-confounds_regressors.tsv")
        assert extract_subject_id_from_path(path) == "sub-003"

    def test_extract_fails_on_no_sub(self):
        """Test that extraction fails when no sub-<id> found."""
        path = Path("/data/processed/ds001/func/confounds.tsv")
        with pytest.raises(MotionExtractionError):
            extract_subject_id_from_path(path)


class TestFindConfounds:
    def test_find_confounds_files(self, mock_env_data_dir):
        """Test finding confounds files in directory structure."""
        files = find_fmriprep_confounds()
        assert len(files) == 2

        # Verify files are TSV
        for f in files:
            assert f.suffix == ".tsv"
            assert "confounds" in f.name.lower()

    def test_find_with_dataset_filter(self, mock_env_data_dir):
        """Test filtering by dataset ID."""
        files = find_fmriprep_confounds(dataset_id="ds000001")
        assert len(files) == 2

    def test_find_no_files_raises(self):
        """Test that missing confounds raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('src.preprocessing.extract_motion.get_data_dir', return_value=tmpdir):
                with pytest.raises(MotionExtractionError, match="not found"):
                    find_fmriprep_confounds()


class TestExtractMotionParameters:
    def test_extract_single_file(self, temp_confounds_dir):
        """Test extracting motion from a single confounds file."""
        confounds_path = temp_confounds_dir / "processed" / "ds000001" / "sub-001" / "func" / "sub-001_task-rest_desc-confounds_regressors.tsv"

        result = extract_motion_parameters(confounds_path)

        assert result['subject_id'] == 'sub-001'
        assert 'translation_x' in result
        assert 'translation_y' in result
        assert 'translation_z' in result
        assert 'rotation_x' in result
        assert 'rotation_y' in result
        assert 'rotation_z' in result

        # Verify mean absolute values
        # trans_x: [0.1, 0.15, 0.2] -> mean abs = 0.15
        assert abs(result['translation_x'] - 0.15) < 0.001
        # rot_x: [0.01, 0.015, 0.02] -> mean abs = 0.015
        assert abs(result['rotation_x'] - 0.015) < 0.001

    def test_extract_missing_columns_raises(self):
        """Test that missing motion columns raise error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            confounds_file = tmpdir_path / "confounds.tsv"
            confounds_file.write_text("other_col\tvalue\n1\t2\n")

            with pytest.raises(MotionExtractionError, match="Could not find motion column"):
                extract_motion_parameters(confounds_file)

    def test_extract_empty_values(self):
        """Test handling of empty/NaN values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            sub_dir = tmpdir_path / "sub-001" / "func"
            sub_dir.mkdir(parents=True)

            confounds_file = sub_dir / "sub-001_confounds.tsv"
            confounds_file.write_text("trans_x\ttrans_y\ttrans_z\trot_x\trot_y\trot_z\n"
                                      "NaN\tNaN\tNaN\tNaN\tNaN\tNaN\n")

            result = extract_motion_parameters(confounds_file)
            # Should default to 0.0 when no valid values
            assert result['translation_x'] == 0.0


class TestWriteMotionCsv:
    def test_write_csv(self, temp_confounds_dir):
        """Test writing motion data to CSV."""
        df = pd.DataFrame({
            'subject_id': ['sub-001', 'sub-002'],
            'translation_x': [0.1, 0.5],
            'translation_y': [0.2, 0.6],
            'translation_z': [0.3, 0.7],
            'rotation_x': [0.01, 0.05],
            'rotation_y': [0.02, 0.06],
            'rotation_z': [0.03, 0.07]
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "motion.csv"
            write_motion_csv(df, output_path)

            assert output_path.exists()
            written_df = pd.read_csv(output_path)
            assert len(written_df) == 2
            assert list(written_df.columns) == list(df.columns)


class TestRunMotionExtraction:
    def test_run_extraction(self, mock_env_data_dir):
        """Test the full extraction pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "motion_output.csv"

            result = run_motion_extraction(output_path=output_path)

            assert result == output_path
            assert output_path.exists()

            # Verify content
            df = pd.read_csv(output_path)
            assert len(df) == 2
            assert 'subject_id' in df.columns
            assert 'translation_x' in df.columns

    def test_run_extraction_creates_directories(self, mock_env_data_dir):
        """Test that output directories are created if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "deep" / "nested" / "output.csv"

            run_motion_extraction(output_path=nested_path)

            assert nested_path.exists()


class TestIntegration:
    def test_full_pipeline(self, mock_env_data_dir):
        """Test the complete pipeline from finding files to writing output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "motion.csv"

            # Run extraction
            run_motion_extraction(output_path=output_path)

            # Verify output
            df = pd.read_csv(output_path)

            # Should have both subjects
            assert len(df) == 2

            # Should have all required columns
            expected_cols = [
                'subject_id', 'translation_x', 'translation_y', 'translation_z',
                'rotation_x', 'rotation_y', 'rotation_z'
            ]
            assert list(df.columns) == expected_cols

            # Verify sub-001 values (mean of [0.1, 0.15, 0.2] = 0.15)
            sub001 = df[df['subject_id'] == 'sub-001']
            assert len(sub001) == 1
            assert abs(sub001.iloc[0]['translation_x'] - 0.15) < 0.001

            # Verify sub-002 values (mean of [0.5, 0.55] = 0.525)
            sub002 = df[df['subject_id'] == 'sub-002']
            assert len(sub002) == 1
            assert abs(sub002.iloc[0]['translation_x'] - 0.525) < 0.001