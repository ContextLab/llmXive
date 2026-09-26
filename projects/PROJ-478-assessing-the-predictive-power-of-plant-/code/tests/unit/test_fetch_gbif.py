"""
Unit tests for GBIF fetching and cleaning pipeline.

Tests cover:
- Data fetching (mocked)
- Cleaning logic (duplicate removal, coordinate validation)
- Spatial thinning
- Error handling
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import json

from src.data.fetch_gbif import (
    fetch_gbif_occurrences,
    clean_occurrences,
    spatial_thinning,
    run_fetch_pipeline
)
from src.utils.logging import get_logger

logger = get_logger(__name__)

@pytest.fixture
def sample_raw_df():
    """Create a sample raw DataFrame with realistic GBIF-like data."""
    return pd.DataFrame({
        'species': ['Helianthus annuus'] * 10,
        'decimalLatitude': [34.0, 34.1, 34.0, 35.0, 35.1, 34.5, 34.6, 34.7, 34.8, 34.9],
        'decimalLongitude': [-118.0, -118.1, -118.0, -117.0, -117.1, -118.5, -118.6, -118.7, -118.8, -118.9],
        'eventDate': ['2020-05-01'] * 10,
        'basisOfRecord': ['OBSERVATION'] * 10
    })

@pytest.fixture
def sample_raw_df_with_duplicates():
    """Create a sample DataFrame with duplicates."""
    return pd.DataFrame({
        'species': ['Helianthus annuus'] * 6,
        'decimalLatitude': [34.0, 34.0, 34.0, 35.0, 35.0, 36.0],
        'decimalLongitude': [-118.0, -118.0, -118.0, -117.0, -117.0, -116.0],
        'eventDate': ['2020-05-01', '2020-05-01', '2020-05-01', '2020-06-01', '2020-06-01', '2020-07-01'],
        'basisOfRecord': ['OBSERVATION'] * 6
    })

@pytest.fixture
def sample_raw_df_with_invalid_coords():
    """Create a sample DataFrame with invalid coordinates."""
    return pd.DataFrame({
        'species': ['Helianthus annuus'] * 5,
        'decimalLatitude': [34.0, np.nan, 95.0, -100.0, 35.0],  # NaN, >90, <-90
        'decimalLongitude': [-118.0, -118.0, -117.0, -200.0, -116.0],  # >180
        'eventDate': ['2020-05-01'] * 5,
        'basisOfRecord': ['OBSERVATION'] * 5
    })

def test_clean_occurrences_duplicate_removal(sample_raw_df_with_duplicates):
    """Test that duplicate records are removed correctly."""
    initial_count = len(sample_raw_df_with_duplicates)
    cleaned_df = clean_occurrences(sample_raw_df_with_duplicates)
    
    # Should remove duplicates based on lat, lon, and date
    assert len(cleaned_df) < initial_count
    assert len(cleaned_df) == 3  # 3 unique combinations
    
    # Verify no duplicates remain
    duplicates = cleaned_df.duplicated(subset=['decimalLatitude', 'decimalLongitude', 'eventDate']).sum()
    assert duplicates == 0

def test_spatial_thinning_logic(sample_raw_df):
    """Test spatial thinning reduces records appropriately."""
    initial_count = len(sample_raw_df)
    thinned_df, stats = spatial_thinning(sample_raw_df, min_distance_km=1.0)
    
    # Thinning should reduce or keep same number of records
    assert len(thinned_df) <= initial_count
    assert stats['initial_count'] == initial_count
    assert stats['final_count'] == len(thinned_df)
    assert 0 <= stats['retention_rate'] <= 1.0

def test_empty_dataframe_handling():
    """Test handling of empty DataFrames."""
    empty_df = pd.DataFrame(columns=['species', 'decimalLatitude', 'decimalLongitude', 'eventDate'])
    
    # Test cleaning
    cleaned = clean_occurrences(empty_df)
    assert len(cleaned) == 0
    
    # Test thinning
    thinned, stats = spatial_thinning(empty_df)
    assert len(thinned) == 0
    assert stats['initial_count'] == 0
    assert stats['final_count'] == 0

def test_fetch_gbif_occurrences_mocked():
    """Test fetch function with mocked API response."""
    mock_response = {
        'results': [
            {
                'species': 'Helianthus annuus',
                'decimalLatitude': 34.0,
                'decimalLongitude': -118.0,
                'eventDate': '2020-05-01',
                'basisOfRecord': 'OBSERVATION'
            }
        ]
    }
    
    with patch('src.data.fetch_gbif.occurrences.search') as mock_search:
        mock_search.return_value = mock_response
        
        df = fetch_gbif_occurrences('Helianthus annuus', max_records=100)
        
        assert len(df) == 1
        assert df['species'].iloc[0] == 'Helianthus annuus'
        mock_search.assert_called_once()

def test_fetch_gbif_no_records():
    """Test error handling when no records are found."""
    with patch('src.data.fetch_gbif.occurrences.search') as mock_search:
        mock_search.return_value = {'results': []}
        
        with pytest.raises(ValueError, match="No occurrence records found"):
            fetch_gbif_occurrences('NonExistent species', max_records=100)

def test_run_fetch_pipeline_structure():
    """Test the overall pipeline structure with mocked components."""
    mock_raw_df = pd.DataFrame({
        'species': ['Helianthus annuus'] * 5,
        'decimalLatitude': [34.0, 34.1, 34.2, 34.3, 34.4],
        'decimalLongitude': [-118.0, -118.1, -118.2, -118.3, -118.4],
        'eventDate': ['2020-05-01'] * 5,
        'basisOfRecord': ['OBSERVATION'] * 5
    })
    
    with patch('src.data.fetch_gbif.fetch_gbif_occurrences', return_value=mock_raw_df):
        with patch('src.data.fetch_gbif.clean_occurrences', return_value=mock_raw_df):
            with patch('src.data.fetch_gbif.spatial_thinning', return_value=(mock_raw_df, {'retention_rate': 1.0})):
                with tempfile.TemporaryDirectory() as tmpdir:
                    results = run_fetch_pipeline(
                        species_name='Helianthus annuus',
                        output_dir=tmpdir,
                        max_records=100,
                        thinning_distance_km=1.0
                    )
                    
                    assert results['status'] != 'failed'
                    assert 'output_files' in results
                    assert len(results['output_files']) == 3
                    
                    # Verify files were created
                    for file_path in results['output_files'].values():
                        assert Path(file_path).exists()

def test_spatial_thinning_retention_rate():
    """Test that spatial thinning reports correct retention rate."""
    # Create points that are far apart (should all be kept)
    df_farthest = pd.DataFrame({
        'species': ['Test'] * 5,
        'decimalLatitude': [30.0, 40.0, 50.0, 60.0, 70.0],
        'decimalLongitude': [-120.0, -110.0, -100.0, -90.0, -80.0],
        'eventDate': ['2020-01-01'] * 5
    })
    
    thinned, stats = spatial_thinning(df_farthest, min_distance_km=1.0)
    assert stats['retention_rate'] == 1.0  # All kept
    
    # Create points that are very close (should be thinned)
    df_close = pd.DataFrame({
        'species': ['Test'] * 10,
        'decimalLatitude': [34.0] * 10,
        'decimalLongitude': [-118.0] * 10,
        'eventDate': ['2020-01-01'] * 10
    })
    
    thinned_close, stats_close = spatial_thinning(df_close, min_distance_km=1.0)
    assert len(thinned_close) == 1  # Only one kept
    assert stats_close['retention_rate'] == 0.1  # 1/10
