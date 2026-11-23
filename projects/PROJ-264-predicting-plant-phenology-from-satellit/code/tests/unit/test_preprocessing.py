import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from src.data.preprocessing import filter_insufficient_data

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe with cloud coverage and observation counts."""
    data = {
        'site_id': ['site_A', 'site_A', 'site_B', 'site_B', 'site_C', 'site_C'],
        'date': pd.to_datetime(['2020-03-01', '2020-04-01', '2020-03-01', '2020-04-01', '2020-03-01', '2020-04-01']),
        'ndvi': [0.2, 0.5, 0.3, 0.6, 0.1, 0.4],
        'cloud_coverage': [0.1, 0.2, 0.9, 0.85, 0.1, 0.2],  # site_B has high coverage
        'observations_count': [10, 12, 0, 0, 5, 6],  # site_B has zero observations
        'phenology_label': [1, 2, None, None, 3, 4]
    }
    return pd.DataFrame(data)

def test_filter_insufficient_data_coverage(sample_dataframe):
    """Test that sites with <80% cloud-free coverage are flagged and excluded."""
    # site_B has high cloud coverage (0.9, 0.85 -> avg > 0.2, so <80% free)
    # site_A and site_C should remain
    filtered_df = filter_insufficient_data(sample_dataframe, coverage_threshold=0.8)
    
    # site_B should be excluded
    assert 'site_B' not in filtered_df['site_id'].unique()
    assert len(filtered_df) == 4  # Only site_A and site_C rows
    assert set(filtered_df['site_id'].unique()) == {'site_A', 'site_C'}

def test_filter_insufficient_data_obs(sample_dataframe):
    """Test that sites with zero observations in critical windows are excluded."""
    # site_B has zero observations
    filtered_df = filter_insufficient_data(sample_dataframe, coverage_threshold=0.8)
    
    # site_B should be excluded due to zero observations
    assert 'site_B' not in filtered_df['site_id'].unique()
    assert len(filtered_df) == 4

def test_filter_insufficient_data_mixed(sample_dataframe):
    """Test filtering with multiple criteria."""
    # Create a dataframe where one site has good coverage but zero obs
    # and another has good obs but bad coverage
    data = {
        'site_id': ['site_A', 'site_A', 'site_B', 'site_B', 'site_C', 'site_C'],
        'date': pd.to_datetime(['2020-03-01', '2020-04-01', '2020-03-01', '2020-04-01', '2020-03-01', '2020-04-01']),
        'ndvi': [0.2, 0.5, 0.3, 0.6, 0.1, 0.4],
        'cloud_coverage': [0.1, 0.2, 0.1, 0.2, 0.9, 0.85],  # site_C has bad coverage
        'observations_count': [10, 12, 0, 0, 5, 6],  # site_B has zero obs
        'phenology_label': [1, 2, None, None, 3, 4]
    }
    df = pd.DataFrame(data)
    
    filtered_df = filter_insufficient_data(df, coverage_threshold=0.8)
    
    # Both site_B (zero obs) and site_C (bad coverage) should be excluded
    assert 'site_B' not in filtered_df['site_id'].unique()
    assert 'site_C' not in filtered_df['site_id'].unique()
    assert len(filtered_df) == 2  # Only site_A rows
    assert set(filtered_df['site_id'].unique()) == {'site_A'}
