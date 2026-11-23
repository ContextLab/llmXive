import os
import sys
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from download_data import optimize_dataframe_dtypes, load_dataframe_chunked, CHUNK_SIZE, TARGET_MEMORY_GB
from config import ConfigError

def test_optimize_dataframe_dtypes():
    """Test that float64 and int64 are converted to float32 and int32."""
    df = pd.DataFrame({
        'float_col': [1.1, 2.2, 3.3],
        'int_col': [1, 2, 3],
        'str_col': ['a', 'b', 'c']
    })
    
    # Verify original dtypes
    assert df['float_col'].dtype == 'float64'
    assert df['int_col'].dtype == 'int64'
    
    optimized_df = optimize_dataframe_dtypes(df)
    
    # Verify optimized dtypes
    assert optimized_df['float_col'].dtype == 'float32'
    assert optimized_df['int_col'].dtype == 'int32'
    assert optimized_df['str_col'].dtype == 'object'

def test_optimize_memory_reduction():
    """Test that memory usage is reduced after optimization."""
    # Create a larger dataframe
    n_rows = 10000
    df = pd.DataFrame({
        'float_col': np.random.rand(n_rows),
        'int_col': np.random.randint(0, 1000, n_rows)
    })
    
    original_mem = df.memory_usage(deep=True).sum()
    optimized_df = optimize_dataframe_dtypes(df)
    optimized_mem = optimized_df.memory_usage(deep=True).sum()
    
    assert optimized_mem < original_mem
    assert (original_mem - optimized_mem) / original_mem > 0.1  # At least 10% reduction

def test_load_dataframe_chunked_csv(tmp_path):
    """Test loading a CSV file in chunks."""
    # Create a test CSV
    test_file = tmp_path / "test.csv"
    df_test = pd.DataFrame({
        'col1': range(1000),
        'col2': range(1000, 2000)
    })
    df_test.to_csv(test_file, index=False)
    
    # Load in chunks
    df_loaded = load_dataframe_chunked(test_file, chunk_size=100)
    
    assert len(df_loaded) == 1000
    assert list(df_loaded.columns) == ['col1', 'col2']

def test_load_dataframe_chunked_parquet(tmp_path):
    """Test loading a Parquet file."""
    # Create a test Parquet
    test_file = tmp_path / "test.parquet"
    df_test = pd.DataFrame({
        'col1': range(500),
        'col2': range(500, 1000)
    })
    df_test.to_parquet(test_file)
    
    # Load
    df_loaded = load_dataframe_chunked(test_file)
    
    assert len(df_loaded) == 500
    assert list(df_loaded.columns) == ['col1', 'col2']

def test_chunk_size_constant():
    """Verify CHUNK_SIZE is set to a reasonable value."""
    assert CHUNK_SIZE == 10000
    assert CHUNK_SIZE > 0

def test_target_memory_constant():
    """Verify TARGET_MEMORY_GB is set to a reasonable value."""
    assert TARGET_MEMORY_GB == 6.0
    assert TARGET_MEMORY_GB > 0