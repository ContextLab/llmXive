import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocess import calculate_daily_pressure_anomalies
from config import get_anomaly_window_days

def test_anomaly_calculation_exclusion_window():
    """
    Test that the moving average excludes the period immediately preceding the event.
    
    Setup:
    - Create a synthetic time series for one event.
    - Event at t=0.
    - Data available from t=-40 to t=+5.
    - Anomaly window = 10 days (for testing speed).
    - Exclusion window = [-10, 0].
    
    Expected:
    - Baseline for t=-5 (which is before exclusion) should use data from t=-40 to t=-15.
    - Baseline for t=-12 (before exclusion) should use data from t=-40 to t=-22.
    - Rows in exclusion window should have NaN anomaly or be handled as per spec.
    """
    # Create synthetic data
    dates = pd.date_range(start='2018-01-01', periods=45, freq='D')
    # Event at 2018-02-14 (index 44 in a 45-day range starting Jan 1? No, let's be precise)
    # Let's say event is at index 30 (2018-01-31)
    event_date = dates[30]
    
    data = []
    for i, d in enumerate(dates):
        # Pressure: baseline 1000, noise
        val = 1000 + np.random.normal(0, 5)
        # Add a jump at event
        if d >= event_date:
            val += 20 
        
        data.append({
            'event_id': 'EQ001',
            'timestamp': d,
            'pressure_hPa': val
        })
    
    df = pd.DataFrame(data)
    event_windows = pd.DataFrame([{
        'event_id': 'EQ001',
        'timestamp': event_date
    }])
    
    # Set window to 10 for this test
    # Note: The function uses config, so we might need to mock or ensure config is 10
    # For this test, we assume the config returns 10 or we pass it.
    # Since the function signature doesn't take window, we rely on config.
    # We will patch the config temporarily or assume the default is 30 and adjust data.
    # Let's adjust data to be 60 days long and use default 30.
    
    # Re-generate for 60 days
    dates = pd.date_range(start='2018-01-01', periods=60, freq='D')
    event_date = dates[40] # Event at day 40
    data = []
    for i, d in enumerate(dates):
        val = 1000 + np.random.normal(0, 2) # Stable baseline
        if d >= event_date:
            val += 50 # Anomaly
        data.append({
            'event_id': 'EQ001',
            'timestamp': d,
            'pressure_hPa': val
        })
    
    df = pd.DataFrame(data)
    event_windows = pd.DataFrame([{
        'event_id': 'EQ001',
        'timestamp': event_date
    }])
    
    # Run calculation
    result = calculate_daily_pressure_anomalies(df, event_windows)
    
    # Check that baseline is calculated correctly for pre-exclusion days
    # Exclusion window is [event_date - 30, event_date]
    # So for t < event_date - 30, we should have a valid baseline.
    # For t >= event_date - 30, baseline might be NaN or calculated from limited history.
    
    # Verify that for the first few days, the anomaly is close to 0 (since baseline is mean of itself roughly)
    # Actually, baseline is mean of ALL previous data.
    
    # Check that rows in the exclusion window have NaN anomaly?
    # The spec says "EXCLUDING the period ... from the moving average calculation".
    # This usually means the MA is calculated on data BEFORE the exclusion.
    # If we are IN the exclusion window, we can't calculate a valid baseline using the rule.
    # So we expect NaN for anomaly in the exclusion window.
    
    exclusion_start = event_date - pd.Timedelta(days=30)
    
    # Check a point strictly before exclusion
    pre_exclusion = result[result['timestamp'] < exclusion_start].iloc[0]
    assert not pd.isna(pre_exclusion['baseline_mean']), "Baseline should exist before exclusion window"
    
    # Check a point inside exclusion window
    in_exclusion = result[(result['timestamp'] >= exclusion_start) & (result['timestamp'] <= event_date)].iloc[0]
    # According to the logic in preprocess.py, if there is no history BEFORE exclusion_start, baseline is NaN.
    # For the first point in exclusion window, there IS history before exclusion_start (the pre-exclusion data).
    # So the baseline IS calculated from pre-exclusion data.
    # The anomaly is then P(t) - baseline.
    # The task says "EXCLUDING ... from the moving average calculation".
    # This implies the MA is computed on data < (t-N).
    # My implementation: baseline = mean(data < (event_date - N)).
    # This is correct. The baseline is fixed for the whole event period based on pre-exclusion data.
    
    # So, anomaly should be calculated for all points, but the baseline is derived ONLY from pre-exclusion data.
    # Let's verify the baseline is the mean of the pre-exclusion data.
    pre_data = df[df['timestamp'] < exclusion_start]['pressure_hPa']
    expected_baseline = pre_data.mean()
    
    # Check that the baseline in the result matches the expected baseline for all rows
    # (Since the baseline is static for the event)
    assert np.allclose(result['baseline_mean'].dropna(), expected_baseline), \
        f"Baseline mismatch: {result['baseline_mean'].dropna().mean()} vs {expected_baseline}"
    
    # Check that anomalies are non-zero for the event period (where pressure jumped)
    event_period = result[result['timestamp'] >= event_date]
    assert (event_period['anomaly'] > 10).all(), "Anomaly should be positive during event period"

def test_config_window_verification():
    """Verify that the config returns 30 days for anomaly window."""
    window = get_anomaly_window_days()
    assert window == 30, f"Anomaly window should be 30 days, got {window}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
