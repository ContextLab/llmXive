"""
Unit tests for the EBSD preprocessing pipeline.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

# Import the functions to test
from data.preprocess import (
    load_ebsd_data, 
    filter_by_confidence, 
    reindex_to_fcc, 
    process_ebsd_dataset,
    CONFIDENCE_THRESHOLD,
    RELIABILITY_THRESHOLD
)
from data.models import EbsdSample

# Fixtures
@pytest.fixture
def sample_df():
    """Create a sample DataFrame with EBSD data."""
    return pd.DataFrame({
        'phi1': [0, 10, 20, 30, 40],
        'Phi': [0, 10, 20, 30, 40],
        'phi2': [0, 10, 20, 30, 40],
        'confidence': [0.9, 0.5, 0.05, 0.15, 0.09],
        'x': [1, 2, 3, 4, 5],
        'y': [1, 2, 3, 4, 5],
        'sample_id': ['s1', 's1', 's1', 's1', 's1'],
        'material': ['Al', 'Al', 'Al', 'Al', 'Al'],
        'reduction': [20, 20, 20, 20, 20]
    })

@pytest.fixture
def temp_csv_file(sample_df):
    """Create a temporary CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_df.to_csv(f, index=False)
        yield Path(f.name)
    os.unlink(f.name)

# Tests
def test_load_ebsd_data(temp_csv_file, sample_df):
    """Test loading EBSD data from CSV."""
    df = load_ebsd_data(temp_csv_file)
    assert len(df) == len(sample_df)
    assert 'confidence' in df.columns
    assert df['confidence'].dtype in ['float64', 'float32']

def test_load_ebsd_data_missing_file():
    """Test loading from a non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_ebsd_data(Path("non_existent_file.csv"))

def test_filter_by_confidence_high(sample_df):
    """Test filtering with a high threshold."""
    df_filtered, fraction_removed = filter_by_confidence(sample_df, threshold=0.8)
    # Only 0.9 is >= 0.8
    assert len(df_filtered) == 1
    assert df_filtered.iloc[0]['confidence'] == 0.9
    assert fraction_removed == 4/5

def test_filter_by_confidence_default(sample_df):
    """Test filtering with default threshold (0.1)."""
    df_filtered, fraction_removed = filter_by_confidence(sample_df)
    # 0.9, 0.5, 0.15 are >= 0.1. 0.05 and 0.09 are < 0.1
    assert len(df_filtered) == 3
    assert fraction_removed == 2/5

def test_filter_by_confidence_empty():
    """Test filtering an empty DataFrame."""
    df = pd.DataFrame(columns=['phi1', 'Phi', 'phi2', 'confidence'])
    df_filtered, fraction = filter_by_confidence(df)
    assert len(df_filtered) == 0
    assert fraction == 1.0

def test_reindex_to_fcc(sample_df):
    """Test re-indexing to FCC symmetry."""
    # This test checks if the function runs without error and returns a DataFrame
    # with the same shape and Euler columns.
    df_reindexed = reindex_to_fcc(sample_df)
    assert df_reindexed.shape == sample_df.shape
    assert 'phi1' in df_reindexed.columns
    assert 'Phi' in df_reindexed.columns
    assert 'phi2' in df_reindexed.columns
    
    # Check that values are within 0-360 range (or fundamental region)
    # orix fundamental region for cubic is [0, 90] for phi1 and phi2, [0, 90] for Phi?
    # Actually, the fundamental region for cubic is more complex, but angles should be valid.
    assert (df_reindexed['phi1'] >= 0).all()
    assert (df_reindexed['Phi'] >= 0).all()
    assert (df_reindexed['phi2'] >= 0).all()

def test_reindex_to_fcc_empty():
    """Test re-indexing an empty DataFrame."""
    df = pd.DataFrame(columns=['phi1', 'Phi', 'phi2', 'confidence'])
    df_reindexed = reindex_to_fcc(df)
    assert df_reindexed.empty

def test_process_ebsd_dataset(temp_csv_file):
    """Test the full processing pipeline."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output.parquet"
        
        # Mock the exclusion logic to prevent actual exclusion in this test
        # We want to test the processing flow, not the exclusion logic which depends on metrics
        with patch('data.preprocess.calculate_reliability_metrics') as mock_metrics, \
             patch('data.preprocess.apply_exclusion_logic') as mock_exclude:
            
            mock_metrics.return_value = {"retention": 0.5}
            mock_exclude.return_value = (False, "OK") # Do not exclude
            
            result = process_ebsd_dataset(temp_csv_file, output_path, reduction_level=20)
            
            assert result["status"] == "success"
            assert output_path.exists()
            assert result["input_points"] == 5
            assert result["output_points"] == 3 # 2 filtered out

def test_process_ebsd_dataset_excluded(temp_csv_file):
    """Test the pipeline when a sample is excluded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output.parquet"
        
        with patch('data.preprocess.calculate_reliability_metrics') as mock_metrics, \
             patch('data.preprocess.apply_exclusion_logic') as mock_exclude:
            
            mock_metrics.return_value = {"retention": 0.2} # Low retention
            mock_exclude.return_value = (True, "Low reliability") # Exclude
            
            result = process_ebsd_dataset(temp_csv_file, output_path, reduction_level=20)
            
            assert result["status"] == "excluded"
            assert not output_path.exists() # Should not be created

def test_process_ebsd_dataset_missing_file():
    """Test processing a non-existent file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "missing.csv"
        output_path = Path(tmpdir) / "output.parquet"
        
        with pytest.raises(FileNotFoundError):
            process_ebsd_dataset(input_path, output_path)