"""
Unit tests for merge.py functionality, specifically the fallback logic.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import pytest

from src.ingest.merge import run_merge_pipeline, merge_datasets
from src.ingest.fallback_aggregator import load_fallback_data

@pytest.fixture
def sample_df_1():
    return pd.DataFrame({
        'experiment_id': ['1', '2'],
        'source': ['NIST', 'NIST'],
        'material_type': ['Steel', 'Aluminum'],
        'milling_speed': [500, 600],
        'milling_time': [10, 20],
        'ball_to_powder_ratio': [5.0, 10.0],
        'youngs_modulus': [200.0, 70.0],
        'density': [7.8, 2.7],
        'd10': [10.0, 15.0],
        'd50': [50.0, 60.0],
        'd90': [100.0, 120.0],
        'process_duration': [24.0, 48.0]
    })

@pytest.fixture
def sample_df_2():
    return pd.DataFrame({
        'experiment_id': ['3', '4'],
        'source': ['MP', 'MP'],
        'material_type': ['Copper', 'Titanium'],
        'milling_speed': [700, 800],
        'milling_time': [30, 40],
        'ball_to_powder_ratio': [15.0, 20.0],
        'youngs_modulus': [110.0, 115.0],
        'density': [8.9, 4.5],
        'd10': [20.0, 25.0],
        'd50': [70.0, 80.0],
        'd90': [140.0, 160.0],
        'process_duration': [72.0, 96.0]
    })

@pytest.fixture
def empty_df():
    return pd.DataFrame()

@pytest.fixture
def mock_fallback_data():
    return pd.DataFrame({
        'experiment_id': ['5', '6', '7'],
        'source': ['UCI', 'UCI', 'UCI'],
        'material_type': ['Zinc', 'Lead', 'Iron'],
        'milling_speed': [900, 1000, 1100],
        'milling_time': [50, 60, 70],
        'ball_to_powder_ratio': [25.0, 30.0, 35.0],
        'youngs_modulus': [100.0, 15.0, 200.0],
        'density': [7.1, 11.3, 7.8],
        'd10': [30.0, 35.0, 40.0],
        'd50': [90.0, 100.0, 110.0],
        'd90': [180.0, 200.0, 220.0],
        'process_duration': [120.0, 144.0, 168.0]
    })

def test_merge_no_duplicates(sample_df_1, sample_df_2):
    """Test merging two non-overlapping DataFrames."""
    result = merge_datasets([sample_df_1, sample_df_2])
    assert len(result) == 4
    assert result['experiment_id'].tolist() == ['1', '2', '3', '4']

def test_merge_with_duplicates(sample_df_1):
    """Test merging DataFrames with duplicate rows."""
    # Create a duplicate of the first row
    duplicate_df = sample_df_1.copy()
    result = merge_datasets([sample_df_1, duplicate_df])
    # Should have only 2 unique rows
    assert len(result) == 2

def test_merge_empty_dataframe_list():
    """Test merging an empty list of DataFrames."""
    result = merge_datasets([])
    assert result.empty

def test_merge_all_empty_dfs(empty_df):
    """Test merging all empty DataFrames."""
    result = merge_datasets([empty_df, empty_df])
    assert result.empty

def test_run_merge_pipeline_with_fallback(mock_fallback_data):
    """Test that run_merge_pipeline correctly uses fallback when count < 150."""
    # Create a small primary dataset (2 rows)
    primary_df = pd.DataFrame({
        'experiment_id': ['1', '2'],
        'source': ['NIST', 'NIST'],
        'material_type': ['Steel', 'Aluminum'],
        'milling_speed': [500, 600],
        'milling_time': [10, 20],
        'ball_to_powder_ratio': [5.0, 10.0],
        'youngs_modulus': [200.0, 70.0],
        'density': [7.8, 2.7],
        'd10': [10.0, 15.0],
        'd50': [50.0, 60.0],
        'd90': [100.0, 120.0],
        'process_duration': [24.0, 48.0]
    })

    # Mock load_fallback_data to return our mock data
    with patch('src.ingest.merge.load_fallback_data', return_value=mock_fallback_data):
        # Run merge with threshold 150
        result = run_merge_pipeline(
            materials_project_df=primary_df,
            nist_df=None,
            arxiv_df=None,
            fallback_threshold=150
        )
        
        # Should have primary (2) + fallback (3) = 5 rows
        assert len(result) == 5
        # Check that fallback source is present
        assert 'UCI Fallback' in result['source'].tolist()

def test_run_merge_pipeline_no_fallback_needed():
    """Test that run_merge_pipeline skips fallback when count >= 150."""
    # Create a large primary dataset (150 rows)
    large_df = pd.DataFrame({
        'experiment_id': [str(i) for i in range(150)],
        'source': ['NIST'] * 150,
        'material_type': ['Steel'] * 150,
        'milling_speed': [500] * 150,
        'milling_time': [10] * 150,
        'ball_to_powder_ratio': [5.0] * 150,
        'youngs_modulus': [200.0] * 150,
        'density': [7.8] * 150,
        'd10': [10.0] * 150,
        'd50': [50.0] * 150,
        'd90': [100.0] * 150,
        'process_duration': [24.0] * 150
    })

    with patch('src.ingest.merge.load_fallback_data') as mock_load:
        result = run_merge_pipeline(
            materials_project_df=large_df,
            nist_df=None,
            arxiv_df=None,
            fallback_threshold=150
        )
        
        # Should have 150 rows
        assert len(result) == 150
        # Fallback should not be called
        mock_load.assert_not_called()

def test_run_merge_pipeline_fallback_unavailable():
    """Test behavior when fallback is needed but unavailable."""
    small_df = pd.DataFrame({
        'experiment_id': ['1'],
        'source': ['NIST'],
        'material_type': ['Steel'],
        'milling_speed': [500],
        'milling_time': [10],
        'ball_to_powder_ratio': [5.0],
        'youngs_modulus': [200.0],
        'density': [7.8],
        'd10': [10.0],
        'd50': [50.0],
        'd90': [100.0],
        'process_duration': [24.0]
    })

    with patch('src.ingest.merge.load_fallback_data', return_value=None):
        result = run_merge_pipeline(
            materials_project_df=small_df,
            nist_df=None,
            arxiv_df=None,
            fallback_threshold=150
        )
        
        # Should return only the small primary data
        assert len(result) == 1