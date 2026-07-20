import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from ingest import join_mpd_mb

@pytest.fixture
def sample_mpd_df():
    data = {
        'track_name': ['Song A', 'Song B', 'Song C', 'Song D'],
        'artist_name': ['Artist X', 'Artist Y', 'Artist Z', 'Artist W'],
        'album_name': ['Album 1', 'Album 2', 'Album 3', 'Album 4'],
        'track_id': ['id1', 'id2', 'id3', 'id4'],
        'playlist_id': ['p1', 'p2', 'p3', 'p4']
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_mb_df():
    data = {
        'track_name': ['Song A', 'Song B', 'Song C', 'Song D'],
        'artist_name': ['Artist X', 'Artist Y', 'Artist Z', 'Artist W'],
        'year': [2020, 2021, None, 2023], # One missing year
        'genre': ['Pop', 'Rock', 'Jazz', 'Pop'],
        'match_type': ['mb_search'] * 4
    }
    return pd.DataFrame(data)

@pytest.fixture
def empty_lastfm_df():
    return pd.DataFrame()

def test_join_mpd_mb_filters_missing_years(sample_mpd_df, sample_mb_df, empty_lastfm_df):
    """
    Test that join_mpd_mb correctly joins data and filters out tracks with missing years.
    """
    result = join_mpd_mb(sample_mpd_df, sample_mb_df, empty_lastfm_df)
    
    # Check row count: 4 total, 1 missing year -> 3 expected
    assert len(result) == 3, f"Expected 3 rows after filtering missing years, got {len(result)}"
    
    # Check that no rows have NaN in 'year'
    assert result['year'].isna().sum() == 0, "Found rows with missing years in result"
    
    # Check specific content
    # 'Song C' had year None, so it should be dropped
    assert 'Song C' not in result['track_name'].values, "Song C (missing year) should be filtered"
    
    # Check that other columns are preserved
    assert 'genre' in result.columns
    assert 'album_name' in result.columns

def test_join_mpd_mb_handles_empty_lastfm(sample_mpd_df, sample_mb_df, empty_lastfm_df):
    """
    Test that the function handles empty Last.fm dataframe gracefully.
    """
    result = join_mpd_mb(sample_mpd_df, sample_mb_df, empty_lastfm_df)
    assert len(result) == 3
    assert 'year' in result.columns

def test_join_mpd_mb_output_file_creation(tmp_path, sample_mpd_df, sample_mb_df, empty_lastfm_df, monkeypatch):
    """
    Test that the function saves the output to the correct file path.
    """
    # Mock the DERIVED_DIR to use a temp directory
    import ingest
    original_derived = ingest.DERIVED_DIR
    ingest.DERIVED_DIR = tmp_path / "data" / "derived"
    ingest.DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        result = join_mpd_mb(sample_mpd_df, sample_mb_df, empty_lastfm_df)
        
        output_file = ingest.DERIVED_DIR / "metadata_mpd.parquet"
        assert output_file.exists(), "Output parquet file was not created"
        
        # Verify content
        loaded_df = pd.read_parquet(output_file)
        assert len(loaded_df) == 3
    finally:
        ingest.DERIVED_DIR = original_derived
