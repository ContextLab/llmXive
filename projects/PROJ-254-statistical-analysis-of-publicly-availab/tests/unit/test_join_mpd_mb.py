"""
Unit tests for join_mpd_mb function.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from ingest import join_mpd_mb

def test_join_mpd_mb_basic():
    """Test basic join and year filtering."""
    # Create mock MPD data
    mpd_data = {
        'track_id': ['1', '2', '3', '4'],
        'year': [2020, 2021, np.nan, 2022], # MPD year
        'playlist_id': ['p1', 'p1', 'p2', 'p2']
    }
    mpd_df = pd.DataFrame(mpd_data)

    # Create mock MB data
    mb_data = {
        'track_id': ['1', '2', '3', '5'],
        'artist': ['A', 'B', 'C', 'D'],
        'title': ['T1', 'T2', 'T3', 'T5'],
        'year': [2020, np.nan, 2023, 2024], # MB year
        'genre': ['Rock', 'Pop', 'Jazz', 'Classical']
    }
    mb_df = pd.DataFrame(mb_data)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "metadata_mpd.parquet"
        
        result = join_mpd_mb(mpd_df, mb_df, output_path)
        
        # Check file exists
        assert output_path.exists()
        
        # Check rows: 
        # Track 1: MPD 2020, MB 2020 -> Keep (2020)
        # Track 2: MPD 2021, MB NaN -> Keep (2021)
        # Track 3: MPD NaN, MB 2023 -> Keep (2023)
        # Track 4: MPD 2022, MB NaN -> Keep (2022) - Wait, MB has no 4, so join is left.
        # Track 5: Not in MPD (left join on MPD), so not in result.
        
        # Expected tracks: 1, 2, 3, 4
        assert len(result) == 4
        
        # Check years
        assert result.loc[result['track_id'] == '1', 'year'].iloc[0] == 2020
        assert result.loc[result['track_id'] == '2', 'year'].iloc[0] == 2021
        assert result.loc[result['track_id'] == '3', 'year'].iloc[0] == 2023
        assert result.loc[result['track_id'] == '4', 'year'].iloc[0] == 2022

def test_join_mpd_mb_all_missing_years():
    """Test filtering when all years are missing."""
    mpd_data = {
        'track_id': ['1', '2'],
        'year': [np.nan, np.nan],
        'playlist_id': ['p1', 'p1']
    }
    mpd_df = pd.DataFrame(mpd_data)

    mb_data = {
        'track_id': ['1', '2'],
        'artist': ['A', 'B'],
        'title': ['T1', 'T2'],
        'year': [np.nan, np.nan],
        'genre': ['Rock', 'Pop']
    }
    mb_df = pd.DataFrame(mb_data)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "metadata_mpd.parquet"
        
        result = join_mpd_mb(mpd_df, mb_df, output_path)
        
        # Should be empty
        assert len(result) == 0

def test_join_mpd_mb_output_schema():
    """Test output schema."""
    mpd_data = {
        'track_id': ['1'],
        'year': [2020],
        'playlist_id': ['p1']
    }
    mpd_df = pd.DataFrame(mpd_data)

    mb_data = {
        'track_id': ['1'],
        'artist': ['A'],
        'title': ['T1'],
        'year': [2020],
        'genre': ['Rock']
    }
    mb_df = pd.DataFrame(mb_data)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "metadata_mpd.parquet"
        
        result = join_mpd_mb(mpd_df, mb_df, output_path)
        
        required_cols = {'track_id', 'year', 'artist', 'title', 'genre', 'playlist_id'}
        assert set(result.columns) == required_cols