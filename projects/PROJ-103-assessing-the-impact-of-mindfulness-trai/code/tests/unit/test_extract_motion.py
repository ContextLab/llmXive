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
    run_motion_extraction,
)


@pytest.fixture
def temp_confounds_dir():
    """Create a temporary directory with mock fMRIPrep confounds files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create mock confounds TSV content
        mock_data = """trans_x\ttrans_y\ttrans_z\trot_x\trot_y\trot_z
        0.1\t0.2\t0.3\t0.01\t0.02\t0.03
        0.15\t0.25\t0.35\t0.015\t0.025\t0.035
        0.2\t0.3\t0.4\t0.02\t0.03\t0.04
        """
        
        # Create a mock subject directory structure
        subject_dir = tmpdir_path / "sub-01" / "func"
        subject_dir.mkdir(parents=True)
        
        confounds_file = subject_dir / "sub-01_task-rest_desc-confounds_timeseries.tsv"
        confounds_file.write_text(mock_data)
        
        # Create another subject
        subject2_dir = tmpdir_path / "sub-02" / "func"
        subject2_dir.mkdir(parents=True)
        
        mock_data2 = """trans_x\ttrans_y\ttrans_z\trot_x\trot_y\trot_z
        0.5\t0.6\t0.7\t0.05\t0.06\t0.07
        0.55\t0.65\t0.75\t0.055\t0.065\t0.075
        """
        confounds_file2 = subject2_dir / "sub-02_task-rest_desc-confounds_timeseries.tsv"
        confounds_file2.write_text(mock_data2)
        
        yield tmpdir_path


@pytest.fixture
def mock_env_data_dir(temp_confounds_dir):
    """Mock get_data_dir to return our temp directory."""
    with patch('src.preprocessing.extract_motion.get_data_dir') as mock_get_dir:
        mock_get_dir.return_value = temp_confounds_dir.parent
        yield mock_get_dir


class TestExtractSubjectId:
    def test_extract_from_standard_path(self):
        """Test extraction from standard fMRIPrep path."""
        path = Path("/data/processed/sub-01/func/sub-01_task-rest_desc-confounds_timeseries.tsv")
        assert extract_subject_id_from_path(path) == "01"
    
    def test_extract_from_nested_path(self):
        """Test extraction from deeply nested path."""
        path = Path("/root/data/sub-999/func/sub-999_task-rest_desc-confounds.tsv")
        assert extract_subject_id_from_path(path) == "999"
    
    def test_fallback_to_parent(self):
        """Test fallback when sub- pattern not found."""
        path = Path("/some/random/path/subdir/file.tsv")
        # Should return the parent directory name
        assert extract_subject_id_from_path(path) == "subdir"


class TestFindConfounds:
    def test_finds_confounds_files(self, temp_confounds_dir):
        """Test that confounds files are found."""
        results = find_fmriprep_confounds(temp_confounds_dir)
        assert len(results) == 2
        assert all("desc-confounds_timeseries.tsv" in str(r) for r in results)
    
    def test_empty_directory(self):
        """Test behavior with empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results = find_fmriprep_confounds(Path(tmpdir))
            assert len(results) == 0
    
    def test_nonexistent_directory(self):
        """Test that nonexistent directory raises error."""
        with pytest.raises(MotionExtractionError):
            find_fmriprep_confounds(Path("/nonexistent/path"))


class TestExtractMotionParameters:
    def test_extract_from_valid_file(self, temp_confounds_dir):
        """Test extraction from a valid confounds file."""
        confounds_file = (
            temp_confounds_dir / "sub-01" / "func" / 
            "sub-01_task-rest_desc-confounds_timeseries.tsv"
        )
        
        result = extract_motion_parameters(confounds_file)
        
        assert result is not None
        assert result['subject_id'] == '01'
        assert 'translation_x' in result
        assert 'translation_y' in result
        assert 'translation_z' in result
        assert 'rotation_x' in result
        assert 'rotation_y' in result
        assert 'rotation_z' in result
        # Check that values are floats
        assert isinstance(result['translation_x'], float)
    
    def test_extract_mean_absolute_values(self, temp_confounds_dir):
        """Test that mean absolute values are computed correctly."""
        confounds_file = (
            temp_confounds_dir / "sub-01" / "func" / 
            "sub-01_task-rest_desc-confounds_timeseries.tsv"
        )
        
        result = extract_motion_parameters(confounds_file)
        
        # Values from mock data:
        # trans_x: [0.1, 0.15, 0.2] -> mean abs = 0.15
        # rot_x: [0.01, 0.015, 0.02] -> mean abs = 0.015
        assert abs(result['translation_x'] - 0.15) < 0.001
        assert abs(result['rotation_x'] - 0.015) < 0.001
    
    def test_missing_columns(self, temp_confounds_dir):
        """Test handling of files with missing columns."""
        # Create a file with missing columns
        bad_data = "trans_x\ttrans_y\n0.1\t0.2\n"
        bad_file = temp_confounds_dir / "sub-01" / "func" / "sub-01_bad.tsv"
        bad_file.write_text(bad_data)
        
        result = extract_motion_parameters(bad_file)
        assert result is None  # Should return None for invalid files
    
    def test_file_not_found(self):
        """Test handling of non-existent file."""
        result = extract_motion_parameters(Path("/nonexistent/file.tsv"))
        assert result is None


class TestWriteMotionCsv:
    def test_writes_valid_csv(self):
        """Test that a valid CSV is written."""
        motion_data = [
            {
                'subject_id': '01',
                'translation_x': 0.15,
                'translation_y': 0.25,
                'translation_z': 0.35,
                'rotation_x': 0.015,
                'rotation_y': 0.025,
                'rotation_z': 0.035,
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "motion.csv"
            result_path = write_motion_csv(motion_data, output_path)
            
            assert result_path.exists()
            df = pd.read_csv(result_path)
            assert len(df) == 1
            assert df['subject_id'].iloc[0] == '01'
            assert 'translation_x' in df.columns
    
    def test_empty_data_raises_error(self):
        """Test that empty data raises an error."""
        with pytest.raises(MotionExtractionError):
            write_motion_csv([])
    
    def test_creates_output_directory(self):
        """Test that output directory is created if missing."""
        motion_data = [
            {
                'subject_id': '01',
                'translation_x': 0.1,
                'translation_y': 0.2,
                'translation_z': 0.3,
                'rotation_x': 0.01,
                'rotation_y': 0.02,
                'rotation_z': 0.03,
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "dir" / "motion.csv"
            result_path = write_motion_csv(motion_data, output_path)
            
            assert result_path.exists()


class TestRunMotionExtraction:
    def test_full_pipeline(self, temp_confounds_dir, mock_env_data_dir):
        """Test the full motion extraction pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "motion_output.csv"
            
            result = run_motion_extraction(
                processed_dir=temp_confounds_dir,
                output_path=output_path
            )
            
            assert result.exists()
            df = pd.read_csv(result)
            assert len(df) == 2  # Two subjects
            assert set(df.columns) == {
                'subject_id', 'translation_x', 'translation_y', 'translation_z',
                'rotation_x', 'rotation_y', 'rotation_z'
            }
    
    def test_no_confounds_raises_error(self):
        """Test that missing confounds raises an error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(MotionExtractionError):
                run_motion_extraction(processed_dir=Path(tmpdir))
    
    def test_no_extracted_data_raises_error(self, temp_confounds_dir):
        """Test that no extracted data raises an error."""
        # Create a directory with no valid confounds
        empty_dir = temp_confounds_dir / "empty"
        empty_dir.mkdir()
        
        with pytest.raises(MotionExtractionError):
            run_motion_extraction(processed_dir=empty_dir)