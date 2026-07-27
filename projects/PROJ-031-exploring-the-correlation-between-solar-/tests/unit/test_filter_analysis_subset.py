"""
Unit tests for the filter_analysis_subset module.

Tests verify that the filtering logic correctly excludes recurrent storms
and produces the expected output dataset.
"""
import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from code.filter_analysis_subset import filter_non_recurrent_storms

@pytest.fixture
def sample_aligned_events():
    """Create a sample aligned events dataset with recurrent flags."""
    data = {
        'event_id': range(1, 11),
        'storm_date': pd.date_range('2020-01-01', periods=10, freq='D'),
        'dst_min': [-50, -100, -150, -80, -120, -200, -30, -90, -140, -160],
        'flare_flux': [1e-4, 1e-3, 1e-2, 1e-4, 1e-3, 1e-2, 1e-5, 1e-4, 1e-3, 1e-2],
        'cme_speed': [400, 800, 1200, 500, 900, 1500, 300, 600, 1000, 1300],
        'is_recurrent': [False, True, False, True, False, False, False, True, False, True]
    }
    return pd.DataFrame(data)

def test_filter_non_recurrent_storms_creates_output_file(sample_aligned_events):
    """Test that the function creates the output CSV file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'aligned_events.csv')
        output_path = os.path.join(tmpdir, 'analysis_subset.csv')
        
        sample_aligned_events.to_csv(input_path, index=False)
        
        result_df = filter_non_recurrent_storms(input_path, output_path)
        
        assert os.path.exists(output_path), "Output file was not created"
        assert isinstance(result_df, pd.DataFrame), "Function did not return a DataFrame"

def test_filter_non_recurrent_storms_excludes_recurrent_events(sample_aligned_events):
    """Test that recurrent events are correctly excluded from the output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'aligned_events.csv')
        output_path = os.path.join(tmpdir, 'analysis_subset.csv')
        
        sample_aligned_events.to_csv(input_path, index=False)
        
        result_df = filter_non_recurrent_storms(input_path, output_path)
        
        # Count expected non-recurrent events (is_recurrent == False)
        expected_count = sample_aligned_events[~sample_aligned_events['is_recurrent'].astype(bool)].shape[0]
        
        assert len(result_df) == expected_count, \
            f"Expected {expected_count} non-recurrent events, got {len(result_df)}"
        
        # Verify no recurrent events in the result
        assert not result_df['is_recurrent'].astype(bool).any(), \
            "Recurrent events were not fully excluded"

def test_filter_non_recurrent_storms_preserves_data_integrity(sample_aligned_events):
    """Test that non-recurrent events retain their original data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'aligned_events.csv')
        output_path = os.path.join(tmpdir, 'analysis_subset.csv')
        
        sample_aligned_events.to_csv(input_path, index=False)
        
        result_df = filter_non_recurrent_storms(input_path, output_path)
        
        # Get indices of non-recurrent events from original data
        non_recurrent_indices = sample_aligned_events[
            ~sample_aligned_events['is_recurrent'].astype(bool)
        ].index.tolist()
        
        # Verify the result contains exactly those events
        original_non_recurrent = sample_aligned_events.loc[non_recurrent_indices]
        
        # Reset index for comparison
        result_df_reset = result_df.reset_index(drop=True)
        original_non_recurrent_reset = original_non_recurrent.reset_index(drop=True)
        
        pd.testing.assert_frame_equal(
            result_df_reset, 
            original_non_recurrent_reset,
            check_dtype=True
        )

def test_filter_non_recurrent_storms_missing_column_raises_error():
    """Test that a missing recurrent flag column raises ValueError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'aligned_events.csv')
        output_path = os.path.join(tmpdir, 'analysis_subset.csv')
        
        # Create data without the is_recurrent column
        data = {
            'event_id': [1, 2, 3],
            'dst_min': [-50, -100, -150]
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)
        
        with pytest.raises(ValueError, match="Recurrent flag column"):
            filter_non_recurrent_storms(input_path, output_path, 'missing_column')

def test_filter_non_recurrent_storms_file_not_found():
    """Test that a missing input file raises FileNotFoundError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'analysis_subset.csv')
        
        with pytest.raises(FileNotFoundError):
            filter_non_recurrent_storms(
                os.path.join(tmpdir, 'nonexistent.csv'),
                output_path
            )

def test_filter_non_recurrent_storms_all_recurrent_raises_error(sample_aligned_events):
    """Test that all recurrent events raises RuntimeError."""
    # Create a dataset where all events are recurrent
    all_recurrent = sample_aligned_events.copy()
    all_recurrent['is_recurrent'] = True
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'aligned_events.csv')
        output_path = os.path.join(tmpdir, 'analysis_subset.csv')
        
        all_recurrent.to_csv(input_path, index=False)
        
        with pytest.raises(RuntimeError, match="Filtering resulted in an empty dataset"):
            filter_non_recurrent_storms(input_path, output_path)
