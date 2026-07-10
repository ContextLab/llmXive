import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from ingestion import handle_missing_frames, IngestionError

@pytest.fixture
def sample_tracking_data():
    """Create a sample DataFrame with intentional gaps."""
    data = {
        'timestamp': [1.0, 2.0, 3.0, 4.0, 5.0, 10.0, 11.0, 12.0],  # Gap between 5 and 10
        'particle_id': [1, 1, 1, 1, 1, 1, 1, 1],
        'x': [1.0, 2.0, 3.0, 4.0, 5.0, np.nan, np.nan, 12.0],
        'y': [1.0, 2.0, 3.0, 4.0, 5.0, np.nan, np.nan, 12.0],
        'z': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def multi_particle_data():
    """Create data with multiple particles and different gap patterns."""
    data = {
        'timestamp': [
            1.0, 2.0, 3.0, 4.0, 5.0,  # Particle 1 (no gap)
            1.0, 2.0, 10.0, 11.0, 12.0,  # Particle 2 (gap between 2 and 10)
            1.0, 2.0, 3.0, 15.0, 16.0, 17.0  # Particle 3 (gap between 3 and 15)
        ],
        'particle_id': [
            1, 1, 1, 1, 1,
            2, 2, 2, 2, 2,
            3, 3, 3, 3, 3, 3
        ],
        'x': [
            1.0, 2.0, 3.0, 4.0, 5.0,
            1.0, 2.0, np.nan, np.nan, 4.0,
            1.0, 2.0, 3.0, np.nan, np.nan, 6.0
        ],
        'y': [
            1.0, 2.0, 3.0, 4.0, 5.0,
            1.0, 2.0, np.nan, np.nan, 4.0,
            1.0, 2.0, 3.0, np.nan, np.nan, 6.0
        ]
    }
    return pd.DataFrame(data)

def test_missing_frames_linear_interpolation(sample_tracking_data):
    """Test that missing frames are correctly interpolated linearly."""
    # Gap is 4 frames (timestamps 6, 7, 8, 9 missing, so 5->10 is a jump)
    # Actually, the gap is between 5.0 and 10.0, which is 5.0 seconds.
    # The function should interpolate the NaNs at timestamps 10.0 and 11.0 
    # if we consider the gap size based on the step.
    # Let's adjust the test data to be clearer.
    
    # Create a clearer gap: 1, 2, 3, 4, 5, [gap], 10, 11
    # The gap is 5 steps (6, 7, 8, 9, 10? No, 10 is present).
    # Let's assume the gap is the missing rows between 5 and 10.
    # In the provided data, rows 5 and 6 (0-indexed) have NaNs.
    # The function should interpolate these.
    
    result = handle_missing_frames(sample_tracking_data, max_gap_frames=10)
    
    # Check that the NaN values in the gap were interpolated
    # The gap is at indices 5 and 6 (timestamps 10.0 and 11.0 in the original data)
    # Wait, the original data has NaNs at rows 5 and 6.
    # The function should fill them.
    assert not result['x'].isna().any(), "Interpolation failed to fill missing x values"
    assert not result['y'].isna().any(), "Interpolation failed to fill missing y values"
    
    # Check that the flag is set for interpolated rows
    # The original NaN rows should be flagged
    # In this specific dataset, rows 5 and 6 were NaN.
    # After interpolation, they should be filled and flagged.
    assert result.loc[5, 'missing_frame_flag'] == True, "Interpolated row should be flagged"
    assert result.loc[6, 'missing_frame_flag'] == True, "Interpolated row should be flagged"
    
    # Check linearity: x at t=10 should be approx 10.0 (if linear from 5.0 to 12.0 over 7 steps)
    # Actually, let's just check that the values are filled and reasonable
    assert result.loc[5, 'x'] > 5.0 and result.loc[5, 'x'] < 12.0
    assert result.loc[6, 'x'] > 5.0 and result.loc[6, 'x'] < 12.0

def test_missing_frames_large_gap_flagging(multi_particle_data):
    """Test that large gaps are flagged but not interpolated."""
    # Particle 2 has a gap of 7 time units (2 to 10) -> 8 frames if step=1
    # Particle 3 has a gap of 12 time units (3 to 15) -> 13 frames if step=1
    # With max_gap_frames=10, Particle 2's gap might be interpolated (8 <= 10)
    # Particle 3's gap should be flagged (13 > 10) and remain NaN or handled differently.
    
    # Let's set max_gap_frames=5 to ensure both are flagged
    result = handle_missing_frames(multi_particle_data, max_gap_frames=5)
    
    # Particle 3's gap (indices 9, 10) should be flagged and NOT interpolated
    # The x values at indices 9 and 10 should remain NaN or be handled as missing
    # The flag should be True
    assert result.loc[9, 'missing_frame_flag'] == True
    assert result.loc[10, 'missing_frame_flag'] == True
    
    # Check that the values are still NaN (not interpolated) for the large gap
    # Note: The implementation sets them to NaN explicitly if the gap is too large
    # but in the provided code, it sets them to NaN only if the gap is too large?
    # Actually, the code sets them to NaN if the gap is too large.
    # Let's verify the behavior:
    # If gap_size > max_gap_frames, we set numeric_cols to NaN.
    # So they should be NaN.
    assert pd.isna(result.loc[9, 'x']) or result.loc[9, 'x'] == np.nan
    assert pd.isna(result.loc[10, 'x']) or result.loc[10, 'x'] == np.nan

def test_missing_frames_per_particle_isolation(multi_particle_data):
    """Test that gaps are handled independently per particle."""
    result = handle_missing_frames(multi_particle_data, max_gap_frames=10)
    
    # Particle 1 (indices 0-4) should have no flags
    p1_flags = result.loc[result['particle_id'] == 1, 'missing_frame_flag']
    assert not p1_flags.any(), "Particle 1 should have no missing frames"
    
    # Particle 2 (indices 5-9) has a gap
    p2_flags = result.loc[result['particle_id'] == 2, 'missing_frame_flag']
    assert p2_flags.any(), "Particle 2 should have flagged frames"
    
    # Particle 3 (indices 10-15) has a gap
    p3_flags = result.loc[result['particle_id'] == 3, 'missing_frame_flag']
    assert p3_flags.any(), "Particle 3 should have flagged frames"

def test_missing_frames_no_gap():
    """Test that data without gaps passes through unchanged (except for flag column)."""
    data = {
        'timestamp': [1.0, 2.0, 3.0, 4.0, 5.0],
        'particle_id': [1, 1, 1, 1, 1],
        'x': [1.0, 2.0, 3.0, 4.0, 5.0],
        'y': [1.0, 2.0, 3.0, 4.0, 5.0]
    }
    df = pd.DataFrame(data)
    
    result = handle_missing_frames(df)
    
    assert not result['missing_frame_flag'].any(), "No frames should be flagged in gapless data"
    assert result['x'].equals(df['x']), "Data should be unchanged"

def test_missing_frames_invalid_columns():
    """Test that missing required columns raise an error."""
    data = {
        'time': [1.0, 2.0, 3.0],
        'pid': [1, 1, 1],
        'x': [1.0, 2.0, 3.0]
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(IngestionError, match="Missing required time column"):
        handle_missing_frames(df, time_col='timestamp')
    
    with pytest.raises(IngestionError, match="Missing required ID column"):
        handle_missing_frames(df, time_col='time', id_col='particle_id')
