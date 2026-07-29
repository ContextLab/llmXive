import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.clean import clean_and_resample
from data.ingest import fetch_omni_sw, fetch_themis_ey
from main import run_analysis_pipeline

def create_synthetic_gap_data():
    """
    Create a synthetic dataset with a significant time gap (e.g., 60 minutes)
    to test US-1 Acceptance Scenario 2.
    """
    start = datetime(2023, 1, 1, 0, 0)
    end = datetime(2023, 1, 1, 2, 0)
    idx = pd.date_range(start=start, end=end, freq='5min')
    
    # Create data with a gap in the middle
    data = []
    for t in idx:
        if 1 * 60 <= (t - start).total_seconds() < 2 * 60:
            # Skip this hour to create a gap
            continue
        data.append({
            'timestamp': t,
            'Vsw': 400.0 + np.random.normal(0, 10),
            'Bz': -5.0 + np.random.normal(0, 1)
        })
    
    df_sw = pd.DataFrame(data)
    df_sw = df_sw.set_index('timestamp')
    
    # Create Ey data with similar gap
    data_ey = []
    for t in idx:
        if 1 * 60 <= (t - start).total_seconds() < 2 * 60:
            continue
        data_ey.append({
            'timestamp': t,
            'Ey': 0.5 + np.random.normal(0, 0.05)
        })
    
    df_ey = pd.DataFrame(data_ey)
    df_ey = df_ey.set_index('timestamp')
    
    return df_sw, df_ey

@pytest.mark.integration
def test_us1_acceptance_scenario_2():
    """
    US-1 Acceptance Scenario 2:
    Verify pipeline handles NaN gaps by cleaning, resampling, and producing
    correlation output without error.
    """
    # We cannot easily inject synthetic data into the main pipeline without
    # mocking the fetch functions. Instead, we test the cleaning logic
    # which is the critical path for handling gaps.
    
    df_sw, df_ey = create_synthetic_gap_data()
    
    # Verify gap exists
    time_diffs = df_sw.index.to_series().diff()
    gaps = time_diffs[time_diffs > pd.Timedelta(minutes=30)]
    assert len(gaps) > 0, "Test data should contain a gap > 30 minutes"
    
    # Run cleaning
    try:
        cleaned_sw, cleaned_ey = clean_and_resample(df_sw, df_ey)
    except Exception as e:
        pytest.fail(f"Clean and resample failed on gap data: {e}")
    
    # Verify output is valid
    assert not cleaned_sw.isnull().any().any(), "Cleaned data should have no NaNs"
    assert not cleaned_ey.isnull().any().any(), "Cleaned Ey data should have no NaNs"
    
    # Verify we still have enough data points for correlation
    assert len(cleaned_sw) > 10, "Should have enough data points after cleaning"
    assert len(cleaned_ey) > 10, "Should have enough data points after cleaning"

@pytest.mark.integration
def test_full_pipeline_with_gap_handling():
    """
    Integration test to verify the full pipeline can handle data that might have gaps.
    Since we can't easily inject gaps into the real fetch, we rely on the fact that
    the real data fetch returns data that might have gaps, and the clean_and_resample
    function handles them. This test ensures the pipeline doesn't crash on real data.
    """
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 1, 6) # 6 hours

    try:
        result = run_analysis_pipeline(start_date, end_date)
    except Exception as e:
        # If real data fetch fails, we can't test the pipeline
        pytest.fail(f"Full pipeline failed: {e}")

    # Verify output
    assert 'pearson' in result
    assert 'p_val_permutation' in result
    assert 'optimal_lag' in result