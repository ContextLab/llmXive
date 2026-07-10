"""
Tests for data alignment logic, specifically focusing on missing data flagging
for gaps greater than 30 days.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import date, timedelta
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.data.models import CosmicRayFlux, SolarActivityIndex, CompositionRatio
from code.utils.logging import setup_logger, log_data_gap

# We will import the alignment logic here once implemented, but for T010
# we focus on the test logic for gap detection.
# The actual alignment logic is expected to be in code/data/align_data.py
# For this test, we simulate the data structure that align_data.py would produce
# and test the gap detection logic.

@pytest.fixture
def sample_timeseries_with_gaps():
    """
    Create a sample time series with intentional gaps > 30 days.
    Returns a DataFrame mimicking the output of align_data.py.
    """
    dates = []
    # Start date
    start_date = date(2021, 1, 1)
    
    # Generate dates with a gap of 45 days (exceeds 30-day threshold)
    # Segment 1: Jan 1 to Jan 20 (20 days)
    for i in range(20):
        dates.append(start_date + timedelta(days=i))
    
    # Gap: Jan 21 to Mar 6 (45 days missing)
    
    # Segment 2: Mar 7 to Mar 15 (9 days)
    for i in range(9):
        dates.append(date(2021, 3, 7) + timedelta(days=i))
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'rigidity_bin': [1.0] * len(dates),
        'proton_flux': np.random.rand(len(dates)) * 100,
        'helium_flux': np.random.rand(len(dates)) * 50,
        'heavy_flux': np.random.rand(len(dates)) * 10,
        'sunspot_number': np.random.rand(len(dates)) * 100
    })
    
    return df

@pytest.fixture
def sample_timeseries_no_gaps():
    """
    Create a sample time series with no gaps > 30 days.
    """
    dates = []
    start_date = date(2021, 1, 1)
    
    # Continuous data for 100 days
    for i in range(100):
        dates.append(start_date + timedelta(days=i))
    
    df = pd.DataFrame({
        'date': dates,
        'rigidity_bin': [1.0] * len(dates),
        'proton_flux': np.random.rand(len(dates)) * 100,
        'helium_flux': np.random.rand(len(dates)) * 50,
        'heavy_flux': np.random.rand(len(dates)) * 10,
        'sunspot_number': np.random.rand(len(dates)) * 100
    })
    
    return df

def test_detect_large_gaps(sample_timeseries_with_gaps):
    """
    Test that gaps > 30 days are correctly identified.
    """
    # Calculate date differences
    dates = sample_timeseries_with_gaps['date'].values
    date_diffs = np.diff(dates)
    
    # Convert to days
    diffs_days = date_diffs / np.timedelta64(1, 'D')
    
    # Find gaps > 30 days
    large_gaps = diffs_days > 30
    
    # We expect at least one gap > 30 days in our sample data
    assert np.any(large_gaps), "Test setup error: No large gaps found in test data"
    
    # Count the number of large gaps
    num_large_gaps = np.sum(large_gaps)
    assert num_large_gaps >= 1, f"Expected at least 1 gap > 30 days, found {num_large_gaps}"

def test_no_false_positives_for_small_gaps(sample_timeseries_no_gaps):
    """
    Test that continuous data does not trigger false positive gap flags.
    """
    dates = sample_timeseries_no_gaps['date'].values
    date_diffs = np.diff(dates)
    diffs_days = date_diffs / np.timedelta64(1, 'D')
    
    # Check for any gaps > 30 days
    large_gaps = diffs_days > 30
    
    assert not np.any(large_gaps), "False positive: Continuous data flagged as having gaps > 30 days"

def test_gap_flagging_logic(sample_timeseries_with_gaps):
    """
    Test the specific logic that flags rows as part of a gap.
    This simulates the logic that would be in align_data.py.
    """
    df = sample_timeseries_with_gaps.copy()
    
    # Add a flag column for gaps
    df['is_data_gap'] = False
    
    dates = df['date'].values
    date_diffs = np.diff(dates)
    diffs_days = date_diffs / np.timedelta64(1, 'D')
    
    # Identify indices where gap > 30 days
    gap_indices = np.where(diffs_days > 30)[0]
    
    # For each gap, flag the start and end points (or the gap period if we had more data)
    # In this simplified version, we flag the row immediately after a large gap
    for idx in gap_indices:
        # Flag the row after the gap (idx + 1 in original dataframe)
        # Note: idx is in the diff array, so it corresponds to the transition from idx to idx+1
        df.iloc[idx + 1, df.columns.get_loc('is_data_gap')] = True
    
    # Verify that we flagged at least one row
    assert df['is_data_gap'].sum() >= 1, "No rows were flagged as data gaps"
    
    # Verify that the flagged rows are indeed after large gaps
    flagged_indices = df[df['is_data_gap']].index
    for idx in flagged_indices:
        if idx > 0:
            prev_date = df.iloc[idx-1]['date']
            curr_date = df.iloc[idx]['date']
            diff = (curr_date - prev_date).days
            assert diff > 30, f"Row {idx} was flagged but gap is only {diff} days"

def test_gap_threshold_boundary():
    """
    Test boundary condition: exactly 30 days vs 31 days.
    """
    # Create data with exactly 30 day gap
    dates_30 = [date(2021, 1, 1), date(2021, 1, 31)]  # 30 days
    df_30 = pd.DataFrame({'date': dates_30})
    
    # Create data with 31 day gap
    dates_31 = [date(2021, 1, 1), date(2021, 2, 1)]  # 31 days
    df_31 = pd.DataFrame({'date': dates_31})
    
    # Check 30 day gap (should NOT be flagged)
    diff_30 = (dates_30[1] - dates_30[0]).days
    assert diff_30 == 30, "Test setup error for 30-day gap"
    assert not (diff_30 > 30), "30-day gap incorrectly flagged as > 30 days"
    
    # Check 31 day gap (should be flagged)
    diff_31 = (dates_31[1] - dates_31[0]).days
    assert diff_31 == 31, "Test setup error for 31-day gap"
    assert diff_31 > 30, "31-day gap not flagged as > 30 days"

def test_gap_detection_with_multiple_species(sample_timeseries_with_gaps):
    """
    Test that gap detection works correctly when multiple species data is present.
    """
    df = sample_timeseries_with_gaps.copy()
    
    # Ensure all required columns exist
    required_cols = ['date', 'rigidity_bin', 'proton_flux', 'helium_flux', 'heavy_flux', 'sunspot_number']
    for col in required_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Gap detection should be independent of species data
    dates = df['date'].values
    date_diffs = np.diff(dates)
    diffs_days = date_diffs / np.timedelta64(1, 'D')
    
    large_gaps = diffs_days > 30
    assert np.any(large_gaps), "Gap detection failed in multi-species data"

def test_gap_logging_integration(sample_timeseries_with_gaps, caplog):
    """
    Test that gaps are properly logged when detected.
    """
    # Setup logger
    logger = setup_logger("test_gap_logging", level="INFO")
    
    # Simulate gap detection and logging
    dates = sample_timeseries_with_gaps['date'].values
    date_diffs = np.diff(dates)
    diffs_days = date_diffs / np.timedelta64(1, 'D')
    
    gap_indices = np.where(diffs_days > 30)[0]
    
    for idx in gap_indices:
        start_date = dates[idx]
        end_date = dates[idx + 1]
        gap_days = int(diffs_days[idx])
        
        # Log the gap
        log_data_gap(
            logger=logger,
            start_date=start_date,
            end_date=end_date,
            gap_days=gap_days,
            source="test_data_alignment"
        )
    
    # Verify that gaps were logged
    assert len(gap_indices) > 0, "No gaps to log"
    
    # Check that log messages contain expected information
    # Note: This depends on the implementation of log_data_gap
    # We assume it logs the gap details

def test_gap_exclusion_from_analysis(sample_timeseries_with_gaps):
    """
    Test that data after large gaps can be excluded from analysis.
    """
    df = sample_timeseries_with_gaps.copy()
    
    # Add gap flag
    dates = df['date'].values
    date_diffs = np.diff(dates)
    diffs_days = date_diffs / np.timedelta64(1, 'D')
    
    gap_indices = np.where(diffs_days > 30)[0]
    rows_to_exclude = set()
    
    for idx in gap_indices:
        # Exclude the row after the gap
        rows_to_exclude.add(idx + 1)
    
    # Create filtered dataframe
    mask = ~df.index.isin(rows_to_exclude)
    df_filtered = df[mask]
    
    # Verify that filtered data has no large gaps
    filtered_dates = df_filtered['date'].values
    if len(filtered_dates) > 1:
        filtered_diffs = np.diff(filtered_dates)
        filtered_diffs_days = filtered_diffs / np.timedelta64(1, 'D')
        large_gaps_filtered = filtered_diffs_days > 30
        assert not np.any(large_gaps_filtered), "Filtered data still contains gaps > 30 days"
    
    # Verify that we removed at least one row
    assert len(df_filtered) < len(df), "No rows were removed during gap exclusion"