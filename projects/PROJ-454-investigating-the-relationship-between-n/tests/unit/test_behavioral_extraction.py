"""
Unit tests for T012c: Behavioral Score Extraction.
"""
import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from config import get_config, get_wcst_variable_name
from code_012c_extract_behavioral_scores import (
    load_raw_parquet_files,
    verify_variable_fit,
    extract_behavioral_scores
)

@pytest.fixture
def temp_raw_dir():
    """Create a temporary directory with mock parquet files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create a valid parquet file
        df_valid = pd.DataFrame({
            'participant_id': ['P01', 'P02', 'P03'],
            'wcst_perseverative_errors': [5, 12, 8],
            'age': [25, 30, 45]
        })
        valid_file = tmpdir / 'ds001.parquet'
        df_valid.to_parquet(valid_file)
        
        # Create an invalid parquet file (missing column)
        df_invalid = pd.DataFrame({
            'participant_id': ['P04'],
            'other_col': [100]
        })
        invalid_file = tmpdir / 'ds002.parquet'
        df_invalid.to_parquet(invalid_file)
        
        yield tmpdir

def test_load_raw_parquet_files(temp_raw_dir):
    """Test loading parquet files."""
    dataframes = load_raw_parquet_files(temp_raw_dir)
    assert 'ds001.parquet' in dataframes
    assert 'ds002.parquet' in dataframes
    assert len(dataframes['ds001.parquet']) == 3

def test_verify_variable_fit(temp_raw_dir):
    """Test filtering datasets by required column."""
    dataframes = load_raw_parquet_files(temp_raw_dir)
    valid_dfs = verify_variable_fit(dataframes, 'wcst_perseverative_errors')
    
    assert 'ds001.parquet' in valid_dfs
    assert 'ds002.parquet' not in valid_dfs
    assert len(valid_dfs) == 1

def test_extract_behavioral_scores(temp_raw_dir):
    """Test extraction logic and CSV generation."""
    dataframes = load_raw_parquet_files(temp_raw_dir)
    valid_dfs = verify_variable_fit(dataframes, 'wcst_perseverative_errors')
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / 'behavioral_scores.csv'
        result_df = extract_behavioral_scores(valid_dfs, output_path, 'wcst_perseverative_errors')
        
        assert output_path.exists()
        assert len(result_df) == 3
        assert 'participant_id' in result_df.columns
        assert 'wcst_perseverative_errors' in result_df.columns
        
        # Check values
        assert result_df.loc[result_df['participant_id'] == 'P01', 'wcst_perseverative_errors'].iloc[0] == 5