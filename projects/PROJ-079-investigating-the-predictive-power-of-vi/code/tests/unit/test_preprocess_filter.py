import pytest
import pandas as pd
import numpy as np
from src.preprocess import filter_samples
from src.config import SEED
import sys
from io import StringIO

@pytest.fixture
def valid_merged_df():
    """Create a valid merged DataFrame with 50 samples."""
    data = {
        'strain_accession': [f'NC_{i:05d}' for i in range(50)],
        'feature_1': np.random.rand(50),
        'isg_score': np.random.rand(50)
    }
    return pd.DataFrame(data)

@pytest.fixture
def merged_df_with_missing():
    """Create a DataFrame with some missing strain_accession values."""
    data = {
        'strain_accession': [f'NC_{i:05d}' if i % 3 != 0 else None for i in range(50)],
        'feature_1': np.random.rand(50),
        'isg_score': np.random.rand(50)
    }
    return pd.DataFrame(data)

@pytest.fixture
def merged_df_too_small():
    """Create a DataFrame with fewer than 30 valid samples."""
    data = {
        'strain_accession': [f'NC_{i:05d}' for i in range(20)],
        'feature_1': np.random.rand(20),
        'isg_score': np.random.rand(20)
    }
    return pd.DataFrame(data)

@pytest.fixture
def merged_df_too_small_with_missing():
    """Create a DataFrame with <30 valid samples after filtering."""
    # 40 rows, but 20 are missing -> 20 valid
    data = {
        'strain_accession': [f'NC_{i:05d}' if i < 20 else None for i in range(40)],
        'feature_1': np.random.rand(40),
        'isg_score': np.random.rand(40)
    }
    return pd.DataFrame(data)

def test_filter_samples_removes_missing(valid_merged_df, merged_df_with_missing):
    """Test that filter_samples removes rows with missing strain links."""
    result = filter_samples(merged_df_with_missing)
    
    # Check that no NaNs exist in strain_accession
    assert result['strain_accession'].isna().sum() == 0
    # Check that we have fewer rows than input
    assert len(result) < len(merged_df_with_missing)
    # Check that all original valid rows are preserved
    original_valid_count = merged_df_with_missing['strain_accession'].notna().sum()
    assert len(result) == original_valid_count

def test_filter_samples_removes_missing_with_gaps():
    """Test filtering with gaps in indices and empty strings."""
    data = {
        'strain_accession': ['NC_00001', '', None, 'NC_00004', 'NC_00005'] * 10, # 50 rows
        'feature_1': np.random.rand(50)
    }
    df = pd.DataFrame(data)
    result = filter_samples(df)
    
    assert result['strain_accession'].isna().sum() == 0
    assert (result['strain_accession'].astype(str).str.strip() == "").sum() == 0
    assert len(result) == 30 # 3 valid per 5 rows * 10

def test_filter_samples_enforces_minimum(valid_merged_df):
    """Test that filter_samples returns the DataFrame when >= 30 samples exist."""
    result = filter_samples(valid_merged_df)
    assert len(result) >= 30
    assert len(result) == len(valid_merged_df)

def test_filter_samples_aborts_if_below_threshold_after_filtering(merged_df_too_small_with_missing, caplog):
    """Test that filter_samples exits with SystemExit if < 30 samples remain."""
    # We expect a SystemExit
    with pytest.raises(SystemExit) as exc_info:
        filter_samples(merged_df_too_small_with_missing)
    
    assert exc_info.value.code == 1
    assert "CRITICAL" in caplog.text
    assert "Aborting pipeline" in caplog.text

def test_filter_samples_preserves_other_columns(valid_merged_df):
    """Test that non-strain columns are preserved."""
    result = filter_samples(valid_merged_df)
    assert list(result.columns) == list(valid_merged_df.columns)
    assert 'feature_1' in result.columns
    assert 'isg_score' in result.columns

def test_filter_samples_with_alternative_column_names():
    """Test behavior when expected column is missing."""
    data = {
        'wrong_column_name': ['NC_00001'] * 50,
        'feature_1': np.random.rand(50)
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(SystemExit) as exc_info:
        filter_samples(df)
    
    assert exc_info.value.code == 1