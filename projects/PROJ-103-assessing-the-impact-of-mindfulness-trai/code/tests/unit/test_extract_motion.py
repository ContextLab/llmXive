"""
Unit tests for motion parameter extraction.
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


class TestExtractSubjectId:
    def test_extract_from_standard_path(self):
        path = Path("/data/processed/sub-01/func/sub-01_desc-confounds_timeseries.tsv")
        assert extract_subject_id_from_path(path) == "sub-01"

    def test_extract_from_nested_path(self):
        path = Path("/project/data/processed/sub-002/func/sub-002_desc-confounds_timeseries.tsv")
        assert extract_subject_id_from_path(path) == "sub-002"

    def test_extract_from_alternative_format(self):
        path = Path("/data/processed/sub-001_task-rest_desc-confounds_timeseries.tsv")
        assert extract_subject_id_from_path(path) == "sub-001"


class TestFindConfounds:
    def test_find_confounds_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create expected directory structure
            processed = Path(tmpdir) / "processed" / "sub-01" / "func"
            processed.mkdir(parents=True)
            confounds = processed / "sub-01_desc-confounds_timeseries.tsv"
            confounds.touch()

            result = find_fmriprep_confounds(Path(tmpdir))
            assert len(result) == 1
            assert confounds in result

    def test_no_confounds_raises_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create empty processed directory
            (Path(tmpdir) / "processed").mkdir(parents=True)

            with pytest.raises(MotionExtractionError, match="No fMRIPrep confounds files found"):
                find_fmriprep_confounds(Path(tmpdir))

    def test_no_processed_dir_raises_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(MotionExtractionError, match="Processed directory not found"):
                find_fmriprep_confounds(Path(tmpdir))


class TestExtractMotionParameters:
    def test_extract_all_parameters(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            confounds_path = Path(tmpdir) / "confounds.tsv"

            # Create a mock confounds file with all required columns
            data = {
                'trans_x': [0.1, 0.2, 0.3, 0.4, 0.5],
                'trans_y': [0.05, 0.1, 0.15, 0.2, 0.25],
                'trans_z': [0.02, 0.04, 0.06, 0.08, 0.1],
                'rot_x': [0.001, 0.002, 0.003, 0.004, 0.005],
                'rot_y': [0.0005, 0.001, 0.0015, 0.002, 0.0025],
                'rot_z': [0.0002, 0.0004, 0.0006, 0.0008, 0.001],
            }
            pd.DataFrame(data).to_csv(confounds_path, sep='\t', index=False)

            result = extract_motion_parameters(confounds_path)

            assert result['subject_id'] == 'tmpdir'  # Fallback name
            assert 'translation_x' in result
            assert 'translation_y' in result
            assert 'translation_z' in result
            assert 'rotation_x' in result
            assert 'rotation_y' in result
            assert 'rotation_z' in result

            # Check that means are computed correctly (absolute values)
            assert result['translation_x'] == pytest.approx(0.3, rel=0.01)

    def test_missing_columns_raises_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            confounds_path = Path(tmpdir) / "confounds.tsv"

            # Create file with missing columns
            data = {'trans_x': [0.1, 0.2], 'other_col': [1, 2]}
            pd.DataFrame(data).to_csv(confounds_path, sep='\t', index=False)

            with pytest.raises(MotionExtractionError, match="Missing motion parameter columns"):
                extract_motion_parameters(confounds_path)

    def test_empty_values_handled(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            confounds_path = Path(tmpdir) / "confounds.tsv"

            data = {
                'trans_x': [None, None, None],
                'trans_y': [None, None, None],
                'trans_z': [None, None, None],
                'rot_x': [None, None, None],
                'rot_y': [None, None, None],
                'rot_z': [None, None, None],
            }
            pd.DataFrame(data).to_csv(confounds_path, sep='\t', index=False)

            result = extract_motion_parameters(confounds_path)

            # Should return 0.0 for empty columns
            assert result['translation_x'] == 0.0


class TestWriteMotionCsv:
    def test_write_csv_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "motion.csv"
            results = [
                {
                    'subject_id': 'sub-01',
                    'translation_x': 0.1, 'translation_y': 0.2, 'translation_z': 0.3,
                    'rotation_x': 0.001, 'rotation_y': 0.002, 'rotation_z': 0.003
                }
            ]

            write_motion_csv(results, output_path)

            assert output_path.exists()
            df = pd.read_csv(output_path)
            assert len(df) == 1
            assert df['subject_id'].iloc[0] == 'sub-01'

    def test_write_csv_creates_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "dir" / "motion.csv"
            results = [
                {
                    'subject_id': 'sub-01',
                    'translation_x': 0.1, 'translation_y': 0.2, 'translation_z': 0.3,
                    'rotation_x': 0.001, 'rotation_y': 0.002, 'rotation_z': 0.003
                }
            ]

            write_motion_csv(results, output_path)

            assert output_path.exists()

    def test_write_empty_results_raises_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "motion.csv"

            with pytest.raises(MotionExtractionError, match="No results to write"):
                write_motion_csv([], output_path)


class TestRunMotionExtraction:
    @patch('src.preprocessing.extract_motion.find_fmriprep_confounds')
    @patch('src.preprocessing.extract_motion.extract_all_motion_parameters')
    @patch('src.preprocessing.extract_motion.write_motion_csv')
    def test_run_extraction_success(self, mock_write, mock_extract, mock_find):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_find.return_value = [Path(tmpdir) / "confounds.tsv"]
            mock_extract.return_value = [
                {
                    'subject_id': 'sub-01',
                    'translation_x': 0.1, 'translation_y': 0.2, 'translation_z': 0.3,
                    'rotation_x': 0.001, 'rotation_y': 0.002, 'rotation_z': 0.003
                }
            ]

            output_path = Path(tmpdir) / "output.csv"
            result = run_motion_extraction(data_root=Path(tmpdir), output_path=output_path)

            assert result == output_path
            mock_find.assert_called_once()
            mock_extract.assert_called_once()
            mock_write.assert_called_once()

    def test_run_with_no_data_root_uses_env(self):
        with patch('src.preprocessing.extract_motion.get_data_dir', return_value="/mock/data"):
            with tempfile.TemporaryDirectory() as tmpdir:
                # Mock the file system to avoid actual file operations
                with patch('src.preprocessing.extract_motion.Path.exists', return_value=False):
                    with pytest.raises(MotionExtractionError):
                        run_motion_extraction()