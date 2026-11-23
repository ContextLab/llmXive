"""
Unit tests for T019: Output data/processed/subjects_cleaned.csv
"""
import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path

from data.output_cleaned_subjects import write_cleaned_subjects, REQUIRED_COLUMNS

def test_write_cleaned_subjects_creates_file():
    """Test that the function creates the output file."""
    df = pd.DataFrame({
        "subject_id": ["S01", "S02"],
        "group": ["musician", "non_musician"],
        "years_of_training": [5.0, 0.0],
        "age": [15, 16],
        "sex": ["M", "F"],
        "motion_score": [0.1, 0.2],
        "ses_score": [50, 45]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.csv"
        result_path = write_cleaned_subjects(df, output_path)

        assert result_path.exists()
        assert result_path == output_path

        loaded_df = pd.read_csv(result_path)
        assert len(loaded_df) == 2
        assert list(loaded_df.columns) == REQUIRED_COLUMNS

def test_write_cleaned_subjects_missing_columns():
    """Test that the function raises ValueError for missing columns."""
    df = pd.DataFrame({
        "subject_id": ["S01"],
        "group": ["musician"],
        "age": [15]
        # Missing years_of_training, sex, motion_score, ses_score
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.csv"
        
        with pytest.raises(ValueError) as excinfo:
            write_cleaned_subjects(df, output_path)
        
        assert "missing required columns" in str(excinfo.value).lower()

def test_write_cleaned_subjects_sorts_by_id():
    """Test that the output is sorted by subject_id."""
    df = pd.DataFrame({
        "subject_id": ["S03", "S01", "S02"],
        "group": ["musician", "non_musician", "musician"],
        "years_of_training": [5.0, 0.0, 2.0],
        "age": [15, 16, 14],
        "sex": ["M", "F", "M"],
        "motion_score": [0.1, 0.2, 0.3],
        "ses_score": [50, 45, 55]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.csv"
        write_cleaned_subjects(df, output_path)
        
        loaded_df = pd.read_csv(output_path)
        assert loaded_df["subject_id"].tolist() == ["S01", "S02", "S03"]

def test_write_cleaned_subjects_excludes_extra_columns():
    """Test that extra columns in input are not written to output."""
    df = pd.DataFrame({
        "subject_id": ["S01"],
        "group": ["musician"],
        "years_of_training": [5.0],
        "age": [15],
        "sex": ["M"],
        "motion_score": [0.1],
        "ses_score": [50],
        "extra_column": ["should_not_appear"],
        "another_extra": [123]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.csv"
        write_cleaned_subjects(df, output_path)
        
        loaded_df = pd.read_csv(output_path)
        assert list(loaded_df.columns) == REQUIRED_COLUMNS
        assert "extra_column" not in loaded_df.columns
        assert "another_extra" not in loaded_df.columns

def test_write_cleaned_subjects_overwrite_false():
    """Test that FileExistsError is raised if file exists and overwrite=False."""
    df = pd.DataFrame({
        "subject_id": ["S01"],
        "group": ["musician"],
        "years_of_training": [5.0],
        "age": [15],
        "sex": ["M"],
        "motion_score": [0.1],
        "ses_score": [50]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.csv"
        
        # Write first time
        write_cleaned_subjects(df, output_path, overwrite=True)
        
        # Try to write again with overwrite=False
        with pytest.raises(FileExistsError):
            write_cleaned_subjects(df, output_path, overwrite=False)

def test_write_cleaned_subjects_creates_directory():
    """Test that the function creates parent directories if they don't exist."""
    df = pd.DataFrame({
        "subject_id": ["S01"],
        "group": ["musician"],
        "years_of_training": [5.0],
        "age": [15],
        "sex": ["M"],
        "motion_score": [0.1],
        "ses_score": [50]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "subdir1" / "subdir2" / "test_output.csv"
        # Ensure subdirs don't exist yet
        assert not Path(tmpdir).exists() # tmpdir exists, but subdirs don't
        
        write_cleaned_subjects(df, output_path)
        
        assert output_path.exists()