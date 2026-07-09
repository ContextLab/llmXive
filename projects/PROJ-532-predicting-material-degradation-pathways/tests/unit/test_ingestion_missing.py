import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Ensure code/ is in path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from ingestion import handle_missing_values

@pytest.fixture
def sample_df():
    """Create a sample DataFrame with missing values."""
    data = {
        'id': [1, 2, 3, 4, 5],
        'Fe': [10.0, 20.0, np.nan, 40.0, 50.0],  # 20% missing -> drop
        'Cr': [1.0, np.nan, 3.0, 4.0, 5.0],      # 20% missing -> drop (if threshold is 5%)
        'Ni': [10.0, 20.0, 30.0, 40.0, 50.0],    # 0% missing
        'C': [0.1, 0.2, 0.3, np.nan, 0.5],      # 20% missing -> drop
        'Type': ['Steel', 'Alloy', 'Steel', 'Alloy', 'Steel']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_df_partial_missing():
    """Create a sample DataFrame with <5% missing values."""
    # 1 missing out of 20 rows = 5%
    rows = 20
    data = {
        'id': range(rows),
        'Fe': [10.0] * rows,
        'Cr': [1.0] * rows,
        'Ni': [10.0] * rows
    }
    df = pd.DataFrame(data)
    # Introduce 1 missing value (5%)
    df.loc[0, 'Fe'] = np.nan
    return df

def test_handle_missing_values_drop_columns(sample_df, tmp_path):
    """Test that columns with >= 5% missing values are dropped."""
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "output.csv"
    
    sample_df.to_csv(input_path, index=False)
    
    # Set threshold to 5% (0.05)
    # In the actual function, the threshold is hardcoded to 0.05
    # We expect 'Fe', 'Cr', 'C' to be dropped because they have 20% missing
    output_path, stats = handle_missing_values(input_path, output_path)
    
    df_result = pd.read_csv(output_path)
    
    # Check that dropped columns are reported
    assert 'Fe' in stats['dropped_columns']
    assert 'Cr' in stats['dropped_columns']
    assert 'C' in stats['dropped_columns']
    
    # Check that result dataframe does not contain dropped columns
    assert 'Fe' not in df_result.columns
    assert 'Cr' not in df_result.columns
    assert 'C' not in df_result.columns
    
    # Check that retained columns are present
    assert 'Ni' in df_result.columns
    assert 'Type' in df_result.columns

def test_handle_missing_values_impute_columns(sample_df_partial_missing, tmp_path):
    """Test that columns with < 5% missing values are imputed with median."""
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "output.csv"
    
    sample_df_partial_missing.to_csv(input_path, index=False)
    
    output_path, stats = handle_missing_values(input_path, output_path)
    
    df_result = pd.read_csv(output_path)
    
    # Check that imputed columns are reported
    assert 'Fe' in stats['imputed_columns']
    
    # Check that the missing value was replaced
    assert not df_result['Fe'].isna().any()
    
    # Check that the value is the median (which is 10.0 in this case)
    assert df_result['Fe'].iloc[0] == 10.0

def test_handle_missing_values_non_numeric_drop_rows(tmp_path):
    """Test that rows with missing non-numeric values are dropped."""
    data = {
        'id': [1, 2, 3, 4],
        'Fe': [10.0, 20.0, 30.0, 40.0],
        'Type': ['Steel', None, 'Steel', 'Alloy']
    }
    df = pd.DataFrame(data)
    
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "output.csv"
    
    df.to_csv(input_path, index=False)
    
    output_path, stats = handle_missing_values(input_path, output_path)
    
    df_result = pd.read_csv(output_path)
    
    # Row with missing 'Type' should be dropped
    assert len(df_result) == 3
    assert 'Type' not in df_result[df_result['id'] == 2].index