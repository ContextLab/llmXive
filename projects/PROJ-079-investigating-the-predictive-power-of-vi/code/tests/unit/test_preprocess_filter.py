import pytest
import pandas as pd
import numpy as np
from src.preprocess import filter_samples
from src.config import SEED

@pytest.fixture
def valid_merged_df():
    """Create a valid merged dataframe with strain accessions."""
    np.random.seed(SEED)
    n_samples = 50
    data = {
        'strain_accession': [f'NC_{i:05d}' for i in range(n_samples)],
        'feature1': np.random.rand(n_samples),
        'feature2': np.random.rand(n_samples),
        'isg_score': np.random.rand(n_samples)
    }
    return pd.DataFrame(data)

@pytest.fixture
def merged_df_with_missing():
    """Create a merged dataframe with some missing strain accessions."""
    np.random.seed(SEED)
    n_samples = 50
    strain_accessions = [f'NC_{i:05d}' for i in range(n_samples)]
    # Set some to None/NaN
    strain_accessions[5] = None
    strain_accessions[10] = np.nan
    strain_accessions[15] = ''
    strain_accessions[20] = '   '
    
    data = {
        'strain_accession': strain_accessions,
        'feature1': np.random.rand(n_samples),
        'feature2': np.random.rand(n_samples),
        'isg_score': np.random.rand(n_samples)
    }
    return pd.DataFrame(data)

@pytest.fixture
def merged_df_too_small():
    """Create a merged dataframe with fewer than 30 valid samples."""
    np.random.seed(SEED)
    n_samples = 25
    data = {
        'strain_accession': [f'NC_{i:05d}' for i in range(n_samples)],
        'feature1': np.random.rand(n_samples),
        'feature2': np.random.rand(n_samples),
        'isg_score': np.random.rand(n_samples)
    }
    return pd.DataFrame(data)

@pytest.fixture
def merged_df_too_small_with_missing():
    """Create a merged dataframe that drops below 30 after filtering."""
    np.random.seed(SEED)
    n_samples = 35
    strain_accessions = [f'NC_{i:05d}' for i in range(n_samples)]
    # Make 10 missing
    for i in [5, 10, 15, 20, 25, 30, 31, 32, 33, 34]:
        strain_accessions[i] = None
    
    data = {
        'strain_accession': strain_accessions,
        'feature1': np.random.rand(n_samples),
        'feature2': np.random.rand(n_samples),
        'isg_score': np.random.rand(n_samples)
    }
    return pd.DataFrame(data)

def test_filter_samples_removes_missing(valid_merged_df):
    """Test that filter_samples removes rows with missing strain links."""
    result = filter_samples(valid_merged_df)
    assert len(result) == len(valid_merged_df)
    assert result['strain_accession'].isna().sum() == 0
    assert (result['strain_accession'].astype(str).str.strip() == '').sum() == 0

def test_filter_samples_removes_missing_with_gaps(merged_df_with_missing):
    """Test that filter_samples correctly removes rows with missing/empty strain links."""
    result = filter_samples(merged_df_with_missing)
    
    # Should have removed 4 samples (indices 5, 10, 15, 20)
    expected_count = 50 - 4
    assert len(result) == expected_count
    
    # All remaining should have valid strain accessions
    assert result['strain_accession'].isna().sum() == 0
    assert (result['strain_accession'].astype(str).str.strip() == '').sum() == 0

def test_filter_samples_enforces_minimum(merged_df_too_small):
    """Test that filter_samples enforces minimum sample count of 30."""
    # This should not raise because we start with 25 valid samples (>=30 check happens after)
    # Actually, 25 < 30, so it should raise
    with pytest.raises(ValueError) as excinfo:
        filter_samples(merged_df_too_small)
    
    assert "below the minimum required 30" in str(excinfo.value)

def test_filter_samples_aborts_if_below_threshold_after_filtering(merged_df_too_small_with_missing):
    """Test that filter_samples aborts if filtering drops below 30 samples."""
    with pytest.raises(ValueError) as excinfo:
        filter_samples(merged_df_too_small_with_missing)
    
    assert "below the minimum required 30" in str(excinfo.value)
    assert "Pipeline must abort" in str(excinfo.value)

def test_filter_samples_preserves_other_columns(valid_merged_df):
    """Test that filter_samples preserves all other columns."""
    result = filter_samples(valid_merged_df)
    
    assert list(result.columns) == list(valid_merged_df.columns)
    assert 'feature1' in result.columns
    assert 'feature2' in result.columns
    assert 'isg_score' in result.columns

def test_filter_samples_with_alternative_column_names():
    """Test filter_samples with alternative strain column names."""
    np.random.seed(SEED)
    n_samples = 40
    
    # Test with 'accession' column
    data = {
        'accession': [f'NC_{i:05d}' for i in range(n_samples)],
        'value': np.random.rand(n_samples)
    }
    df = pd.DataFrame(data)
    result = filter_samples(df)
    assert len(result) == n_samples
    assert result['accession'].isna().sum() == 0
