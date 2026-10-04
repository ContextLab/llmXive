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
        tmpdir = Path(tmpdir)
        
        # Create a subject directory
        sub_dir = tmpdir / "sub-01"
        sub_dir.mkdir()
        
        # Create a mock confounds TSV file
        confounds_content = """#dummy comment
        trans_x\ttrans_y\ttrans_z\trot_x\trot_y\trot_z
        0.1\t0.2\t0.3\t0.01\t0.02\t0.03
        0.5\t0.6\t0.7\t0.05\t0.06\t0.07
        1.5\t0.1\t0.1\t0.10\t0.01\t0.01
        """
        confounds_file = sub_dir / "sub-01_task-rest_desc-confounds_timeseries.tsv"
        confounds_file.write_text(confounds_content)

        # Create another subject
        sub2_dir = tmpdir / "sub-02"
        sub2_dir.mkdir()
        confounds_file2 = sub2_dir / "sub-02_task-rest_desc-confounds_timeseries.tsv"
        confounds_file2.write_text(confounds_content)

        yield tmpdir


@pytest.fixture
def mock_env_data_dir():
    """Mock environment data directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestExtractSubjectId:
    def test_extract_from_path_standard(self):
        path = Path("/data/processed/sub-01/func/sub-01_task-rest_desc-confounds.tsv")
        assert extract_subject_id_from_path(path) == "sub-01"

    def test_extract_from_filename(self):
        path = Path("/data/sub-05_confounds.tsv")
        assert extract_subject_id_from_path(path) == "sub-05"

    def test_extract_invalid_path_raises(self):
        path = Path("/data/no_subject_id.tsv")
        with pytest.raises(MotionExtractionError):
            extract_subject_id_from_path(path)


class TestFindConfounds:
    def test_find_confounds_exists(self, temp_confounds_dir):
        result = find_fmriprep_confounds(temp_confounds_dir, "sub-01")
        assert result is not None
        assert result.exists()
        assert "sub-01" in str(result)

    def test_find_confounds_not_found(self, temp_confounds_dir):
        result = find_fmriprep_confounds(temp_confounds_dir, "sub-99")
        assert result is None


class TestExtractMotionParameters:
    def test_extract_parameters_success(self, temp_confounds_dir):
        confounds_path = temp_confounds_dir / "sub-01" / "sub-01_task-rest_desc-confounds_timeseries.tsv"
        df = extract_motion_parameters(confounds_path)
        
        assert "subject_id" in df.columns
        assert "translation_x" in df.columns
        assert "translation_y" in df.columns
        assert "translation_z" in df.columns
        assert "rotation_x" in df.columns
        assert "rotation_y" in df.columns
        assert "rotation_z" in df.columns
        
        assert df["subject_id"].iloc[0] == "sub-01"
        # Check max values from mock data
        # trans_x: max(0.1, 0.5, 1.5) = 1.5
        assert df["translation_x"].iloc[0] == 1.5

    def test_extract_missing_columns(self, temp_confounds_dir):
        # Create a file with missing columns
        bad_content = "trans_x\tother_col\n0.1\t0.2\n"
        bad_file = temp_confounds_dir / "sub-03" / "bad_confounds.tsv"
        bad_file.parent.mkdir()
        bad_file.write_text(bad_content)
        
        with pytest.raises(MotionExtractionError):
            extract_motion_parameters(bad_file)

    def test_file_not_found(self):
        with pytest.raises(MotionExtractionError):
            extract_motion_parameters(Path("/nonexistent/file.tsv"))


class TestWriteMotionCsv:
    def test_write_csv_creates_file(self, temp_confounds_dir, mock_env_data_dir):
        df = pd.DataFrame({
            "subject_id": ["sub-01"],
            "translation_x": [1.5],
            "translation_y": [0.6],
            "translation_z": [0.7],
            "rotation_x": [0.1],
            "rotation_y": [0.06],
            "rotation_z": [0.07]
        })
        output_path = mock_env_data_dir / "results" / "motion.csv"
        
        write_motion_csv(df, output_path)
        
        assert output_path.exists()
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 1
        assert loaded_df["subject_id"].iloc[0] == "sub-01"


class TestRunMotionExtraction:
    def test_run_extraction_full_pipeline(self, temp_confounds_dir, mock_env_data_dir):
        output_path = mock_env_data_dir / "results" / "motion_params.csv"
        
        result_df = run_motion_extraction(temp_confounds_dir, output_path)
        
        assert len(result_df) == 2  # sub-01 and sub-02
        assert "subject_id" in result_df.columns
        assert output_path.exists()

    def test_run_extraction_empty_dir(self, mock_env_data_dir):
        output_path = mock_env_data_dir / "results" / "motion.csv"
        result_df = run_motion_extraction(mock_env_data_dir, output_path)
        assert result_df.empty
        assert output_path.exists()