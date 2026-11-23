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
    """Create a temporary directory structure mimicking fMRIPrep output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        # Create structure: dataset_id/sub-01/func/...
        sub_dir = base / "ds000001" / "sub-01" / "func"
        sub_dir.mkdir(parents=True)

        # Create a mock confounds file
        confounds_file = sub_dir / "sub-01_task-rest_desc-confounds_timeseries.tsv"
        data = {
            "trans_x": [0.1, 0.2, 0.15],
            "trans_y": [0.05, 0.1, 0.08],
            "trans_z": [0.02, 0.03, 0.01],
            "rot_x": [0.001, 0.002, 0.0015],
            "rot_y": [0.0005, 0.001, 0.0008],
            "rot_z": [0.0002, 0.0003, 0.0001],
            "other_col": [1, 2, 3]
        }
        pd.DataFrame(data).to_csv(confounds_file, sep="\t", index=False)

        yield base


@pytest.fixture
def mock_env_data_dir(temp_confounds_dir):
    """Mock the get_data_dir function to return the temp directory."""
    with patch("src.preprocessing.extract_motion.get_data_dir") as mock_get_dir:
        mock_get_dir.return_value = str(temp_confounds_dir)
        yield temp_confounds_dir


class TestExtractSubjectId:
    def test_extract_from_standard_path(self):
        path = Path("/data/processed/ds000001/sub-01/func/file.tsv")
        assert extract_subject_id_from_path(path) == "sub-01"

    def test_extract_from_nested_path(self):
        path = Path("/very/deep/path/sub-42/func/sub-42_task-rest_desc-confounds_timeseries.tsv")
        assert extract_subject_id_from_path(path) == "sub-42"

    def test_extract_from_filename(self):
        path = Path("sub-05_task-rest_desc-confounds_timeseries.tsv")
        assert extract_subject_id_from_path(path) == "sub-05"

    def test_invalid_path_raises(self):
        path = Path("random_file.txt")
        with pytest.raises(MotionExtractionError):
            extract_subject_id_from_path(path)


class TestFindConfounds:
    def test_finds_confounds_files(self, temp_confounds_dir):
        files = find_fmriprep_confounds(temp_confounds_dir, "ds000001")
        assert len(files) == 1
        assert "sub-01" in str(files[0])
        assert "desc-confounds_timeseries.tsv" in str(files[0])

    def test_no_files_raises(self, temp_confounds_dir):
        with pytest.raises(MotionExtractionError):
            find_fmriprep_confounds(temp_confounds_dir, "non_existent_ds")


class TestExtractMotionParameters:
    def test_extract_valid_parameters(self, temp_confounds_dir):
        confounds_file = temp_confounds_dir / "ds000001" / "sub-01" / "func" / "sub-01_task-rest_desc-confounds_timeseries.tsv"
        df = extract_motion_parameters(confounds_file)

        assert df is not None
        assert "subject_id" in df.columns
        assert "translation_x" in df.columns
        assert "rotation_z" in df.columns
        assert len(df) == 3
        assert df["subject_id"].iloc[0] == "sub-01"

    def test_missing_columns_returns_none(self, temp_confounds_dir):
        # Create a file with missing columns
        bad_file = temp_confounds_dir / "ds000001" / "sub-02" / "func" / "sub-02_task-rest_desc-confounds_timeseries.tsv"
        bad_file.parent.mkdir(parents=True)
        pd.DataFrame({"trans_x": [1, 2], "other": [3, 4]}).to_csv(bad_file, sep="\t", index=False)

        result = extract_motion_parameters(bad_file)
        assert result is None

    def test_malformed_file_returns_none(self, temp_confounds_dir):
        bad_file = temp_confounds_dir / "ds000001" / "sub-03" / "func" / "sub-03_task-rest_desc-confounds_timeseries.tsv"
        bad_file.parent.mkdir(parents=True)
        bad_file.write_text("This is not a TSV file")

        result = extract_motion_parameters(bad_file)
        assert result is None


class TestWriteMotionCsv:
    def test_writes_csv_correctly(self, temp_confounds_dir):
        df = pd.DataFrame({
            "subject_id": ["sub-01"],
            "translation_x": [0.1],
            "translation_y": [0.05],
            "translation_z": [0.02],
            "rotation_x": [0.001],
            "rotation_y": [0.0005],
            "rotation_z": [0.0002]
        })
        output_path = temp_confounds_dir / "output" / "motion.csv"
        write_motion_csv(df, output_path)

        assert output_path.exists()
        loaded_df = pd.read_csv(output_path)
        assert len(loaded_df) == 1
        assert loaded_df["subject_id"].iloc[0] == "sub-01"


class TestRunMotionExtraction:
    def test_full_extraction(self, mock_env_data_dir):
        with patch("src.preprocessing.extract_motion.find_fmriprep_confounds") as mock_find, \
             patch("src.preprocessing.extract_motion.extract_motion_parameters") as mock_extract, \
             patch("src.preprocessing.extract_motion.write_motion_csv") as mock_write:

            mock_find.return_value = [mock_env_data_dir / "ds000001" / "sub-01" / "func" / "file.tsv"]
            mock_df = pd.DataFrame({"subject_id": ["sub-01"], "translation_x": [0.1]})
            mock_extract.return_value = mock_df

            result_path = run_motion_extraction("ds000001")

            assert result_path.exists()
            mock_find.assert_called_once()
            mock_extract.assert_called_once()
            mock_write.assert_called_once()

    def test_empty_extraction_raises(self, mock_env_data_dir):
        with patch("src.preprocessing.extract_motion.find_fmriprep_confounds") as mock_find, \
             patch("src.preprocessing.extract_motion.extract_motion_parameters") as mock_extract:

            mock_find.return_value = [mock_env_data_dir / "ds000001" / "sub-01" / "func" / "file.tsv"]
            mock_extract.return_value = None

            with pytest.raises(MotionExtractionError):
                run_motion_extraction("ds000001")