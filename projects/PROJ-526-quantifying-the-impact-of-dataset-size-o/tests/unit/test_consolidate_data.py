"""
Unit tests for data consolidation logic.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from consolidate_data import (
    load_processed_data,
    optimize_dataframe_memory,
    save_consolidated_data,
    MEMORY_LIMIT_GB
)
from config import Config

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        processed_dir = data_dir / 'processed'
        processed_dir.mkdir()
        
        # Create test data files
        df1 = pd.DataFrame({
            'material_id': [1, 2, 3],
            'property_value': [1.1, 2.2, 3.3],
            'composition': ['H2O', 'CO2', 'NaCl']
        })
        df1.to_parquet(processed_dir / 'property_a_processed.parquet')
        
        df2 = pd.DataFrame({
            'material_id': [4, 5],
            'property_value': [4.4, 5.5],
            'composition': ['Fe2O3', 'SiO2']
        })
        df2.to_csv(processed_dir / 'property_b_raw.csv')
        
        yield data_dir
        
        # Cleanup handled by TemporaryDirectory
    
def test_load_processed_data(temp_data_dir):
    """Test loading processed data files."""
    dataframes = load_processed_data(temp_data_dir)
    
    assert len(dataframes) == 2
    assert 'property_name' in dataframes[0].columns
    assert 'property_name' in dataframes[1].columns
    assert len(dataframes[0]) == 3
    assert len(dataframes[1]) == 2
    
def test_optimize_dataframe_memory():
    """Test memory optimization logic."""
    df = pd.DataFrame({
        'int_col': [1, 2, 3, 4, 5],
        'float_col': [1.1, 2.2, 3.3, 4.4, 5.5],
        'object_col': ['a', 'b', 'c', 'd', 'e']
    })
    
    optimized = optimize_dataframe_memory(df)
    
    # Check that optimization occurred
    assert optimized['int_col'].dtype in ['int32', 'int64']
    assert optimized['float_col'].dtype in ['float32', 'float64']
    
def test_save_consolidated_data(temp_data_dir):
    """Test saving consolidated data."""
    dataframes = load_processed_data(temp_data_dir)
    
    output_path = temp_data_dir / 'processed' / 'test_master.parquet'
    result_path = save_consolidated_data(dataframes, output_path)
    
    assert Path(result_path).exists()
    assert 'test_master.parquet' in result_path
    
    # Verify content
    loaded = pd.read_parquet(result_path)
    assert len(loaded) == 5
    assert 'property_name' in loaded.columns
    
def test_csv_fallback():
    """Test CSV fallback when requested."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        processed_dir = data_dir / 'processed'
        processed_dir.mkdir()
        
        df = pd.DataFrame({
            'material_id': [1, 2, 3],
            'property_value': [1.1, 2.2, 3.3]
        })
        df.to_parquet(processed_dir / 'test_processed.parquet')
        
        dataframes = load_processed_data(data_dir)
        output_path = data_dir / 'processed' / 'test_master.parquet'
        
        # Force CSV fallback
        result_path = save_consolidated_data(dataframes, output_path, use_csv_fallback=True)
        
        assert result_path.endswith('.csv')
        assert Path(result_path).exists()
        
def test_empty_directory():
    """Test handling of empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        processed_dir = data_dir / 'processed'
        processed_dir.mkdir()
        
        with pytest.raises(FileNotFoundError):
            load_processed_data(data_dir)
    
def test_mixed_dtypes_optimization():
    """Test optimization with mixed data types."""
    df = pd.DataFrame({
        'low_cardinality': ['a', 'a', 'b', 'b', 'c'],
        'high_cardinality': ['x' + str(i) for i in range(5)],
        'large_float': [1e10, 2e10, 3e10, 4e10, 5e10],
        'small_float': [0.1, 0.2, 0.3, 0.4, 0.5]
    })
    
    optimized = optimize_dataframe_memory(df)
    
    # Low cardinality should become category
    assert optimized['low_cardinality'].dtype.name == 'category'
    
    # High cardinality stays object
    assert optimized['high_cardinality'].dtype == 'object'
    
    # Large float might stay float64 if out of float32 range
    # Small float should become float32
    assert optimized['small_float'].dtype == np.float32