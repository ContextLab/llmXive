"""
Unit tests for EBSD preprocessing pipeline.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from code.data.preprocess import (
    load_ebsd_data,
    filter_by_confidence,
    reindex_to_fcc,
    process_ebsd_dataset,
    CONFIDENCE_THRESHOLD,
    RELIABILITY_THRESHOLD
)
from code.data.models import EbsdSample

@pytest.fixture
def sample_ebsd_data():
    """Create sample EBSD data for testing."""
    return pd.DataFrame({
        'sample_id': ['S1', 'S1', 'S1', 'S2', 'S2', 'S2', 'S2'],
        'phi1': [0.0, 45.0, 90.0, 0.0, 45.0, 90.0, 135.0],
        'Phi': [0.0, 45.0, 90.0, 0.0, 45.0, 90.0, 135.0],
        'phi2': [0.0, 45.0, 90.0, 0.0, 45.0, 90.0, 135.0],
        'confidence': [0.9, 0.5, 0.05, 0.8, 0.3, 0.09, 0.95],
        'reduction': [20, 20, 20, 40, 40, 40, 40],
        'material': ['Al', 'Al', 'Al', 'Cu', 'Cu', 'Cu', 'Cu']
    })

@pytest.fixture
def temp_parquet_file(sample_ebsd_data):
    """Create a temporary Parquet file with sample data."""
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
        sample_ebsd_data.to_parquet(f.name, index=False)
        yield f.name
        os.unlink(f.name)

def test_filter_by_confidence_threshold(sample_ebsd_data):
    """Test that confidence filtering works correctly."""
    filtered, excluded = filter_by_confidence(sample_ebsd_data, threshold=0.1)
    
    # Check that all filtered rows have confidence >= 0.1
    assert all(filtered['confidence'] >= 0.1)
    
    # Check that all excluded rows have confidence < 0.1
    assert all(excluded['confidence'] < 0.1)
    
    # Check counts: 20, 0.05, 0.09 should be excluded (3 rows)
    assert len(excluded) == 3
    assert len(filtered) == 4

def test_filter_by_confidence_no_column():
    """Test behavior when confidence column is missing."""
    df_no_conf = pd.DataFrame({
        'phi1': [0.0, 45.0],
        'Phi': [0.0, 45.0],
        'phi2': [0.0, 45.0]
    })
    
    filtered, excluded = filter_by_confidence(df_no_conf)
    
    # Should return original data and empty excluded
    assert len(filtered) == len(df_no_conf)
    assert len(excluded) == 0

def test_reindex_to_fcc_symmetry(sample_ebsd_data):
    """Test that orientations are re-indexed to FCC symmetry."""
    df_filtered, _ = filter_by_confidence(sample_ebsd_data, threshold=0.1)
    df_reindexed = reindex_to_fcc(df_filtered)
    
    # Check that Euler angles are still valid (0-360 range)
    assert all((df_reindexed['phi1'] >= 0) & (df_reindexed['phi1'] <= 360))
    assert all((df_reindexed['Phi'] >= 0) & (df_reindexed['Phi'] <= 180))
    assert all((df_reindexed['phi2'] >= 0) & (df_reindexed['phi2'] <= 360))
    
    # Check that we still have the same number of rows
    assert len(df_reindexed) == len(df_filtered)
    
    # Check that columns are preserved
    assert set(df_reindexed.columns) == set(df_filtered.columns)

def test_reindex_missing_euler_columns():
    """Test behavior when Euler angle columns are missing."""
    df_no_euler = pd.DataFrame({
        'confidence': [0.5, 0.8],
        'sample_id': ['S1', 'S2']
    })
    
    result = reindex_to_fcc(df_no_euler)
    
    # Should return original data unchanged
    assert len(result) == len(df_no_euler)
    assert 'phi1' not in result.columns

def test_process_ebsd_dataset(temp_parquet_file):
    """Test the full preprocessing pipeline."""
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as out:
        output_path = out.name
    
    try:
        stats = process_ebsd_dataset(
            temp_parquet_file,
            output_path,
            reduction_levels=[20, 40]
        )
        
        # Check stats
        assert stats['input_rows'] == 7
        assert stats['filtered_by_confidence'] == 3
        assert stats['final_rows'] == 4
        assert stats['output_path'] == output_path
        
        # Check output file exists
        assert Path(output_path).exists()
        
        # Check output content
        df_out = pd.read_parquet(output_path)
        assert len(df_out) == 4
        assert all(df_out['confidence'] >= 0.1)
        
    finally:
        if Path(output_path).exists():
            os.unlink(output_path)

def test_process_ebsd_dataset_with_exclusion():
    """Test exclusion logic for low-reliability samples."""
    # Create data where one sample has >50% low confidence
    df = pd.DataFrame({
        'sample_id': ['S1', 'S1', 'S1', 'S2', 'S2', 'S2', 'S2', 'S2'],
        'phi1': [0.0, 45.0, 90.0, 0.0, 45.0, 90.0, 135.0, 180.0],
        'Phi': [0.0, 45.0, 90.0, 0.0, 45.0, 90.0, 135.0, 180.0],
        'phi2': [0.0, 45.0, 90.0, 0.0, 45.0, 90.0, 135.0, 180.0],
        'confidence': [0.9, 0.5, 0.05, 0.8, 0.3, 0.09, 0.95, 0.08],
        'reduction': [20, 20, 20, 40, 40, 40, 40, 40],
        'material': ['Al', 'Al', 'Al', 'Cu', 'Cu', 'Cu', 'Cu', 'Cu']
    })
    
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
        f_path = f.name
        df.to_parquet(f.name, index=False)
    
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as out:
        output_path = out.name
    
    try:
        stats = process_ebsd_dataset(f_path, output_path)
        
        # S1 has 1/3 low confidence (33%) - should be kept
        # S2 has 3/5 low confidence (60%) - should be excluded
        # Final should have only S1 rows (2 rows: 0.9 and 0.5)
        assert stats['excluded_samples'] >= 1  # At least S2 excluded
        
        df_out = pd.read_parquet(output_path)
        assert len(df_out) <= 2  # Only S1 should remain
        
    finally:
        if Path(f_path).exists():
            os.unlink(f_path)
        if Path(output_path).exists():
            os.unlink(output_path)

def test_load_ebsd_data_invalid_file():
    """Test error handling for non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_ebsd_data('/nonexistent/path/file.parquet')

def test_load_ebsd_data_unsupported_format():
    """Test error handling for unsupported file format."""
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b"test")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError):
            load_ebsd_data(temp_path)
    finally:
        os.unlink(temp_path)