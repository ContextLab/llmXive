"""
Integration test for T026: Execute lag-search on synthetic dataset.
Verifies that the pipeline identifies the true lag (45 min) within ±1 min tolerance.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import pytest

# Add project root to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from code.data.lag import calculate_physics_lag, apply_lag_shift
from code.analysis.correlation import calculate_correlation
from code.analysis.lag_search import find_optimal_lag
from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP


def generate_synthetic_dataset(true_lag_minutes: int = 45, duration_hours: int = 24, cadence_minutes: int = 5):
    """
    Generates a synthetic dataset where Ey is a lagged version of Vsw plus noise.
    
    Args:
        true_lag_minutes: The lag applied to Vsw to create Ey.
        duration_hours: Total duration of the dataset.
        cadence_minutes: Time step between samples.
        
    Returns:
        Tuple of (Vsw_df, Ey_df) with aligned timestamps.
    """
    n_samples = int((duration_hours * 60) / cadence_minutes)
    timestamps = [datetime(2023, 6, 15) + timedelta(minutes=i * cadence_minutes) for i in range(n_samples)]
    
    # Generate Vsw signal: sinusoidal with noise
    t = np.arange(n_samples)
    base_freq = 2 * np.pi / (24 * 60 / cadence_minutes)  # 24-hour period in samples
    vsw_signal = 400 + 100 * np.sin(base_freq * t) + np.random.normal(0, 10, n_samples)
    
    # Create Ey signal: Vsw shifted by true_lag_minutes + noise
    lag_steps = true_lag_minutes // cadence_minutes
    # Shift Vsw to create Ey (Ey follows Vsw after lag)
    # If Vsw at t=0 causes Ey at t=lag, then Ey[t] ~ Vsw[t - lag]
    # To simulate this: Ey[t] = Vsw[t - lag_steps]
    # For the first lag_steps samples, we pad with mean or ignore
    vsw_padded = np.concatenate([np.full(lag_steps, np.nan), vsw_signal[:-lag_steps]])
    ey_signal = vsw_padded + np.random.normal(0, 5, n_samples)
    
    vsw_df = pd.DataFrame({'timestamp': timestamps, 'Vsw': vsw_signal})
    ey_df = pd.DataFrame({'timestamp': timestamps, 'Ey': ey_signal})
    
    return vsw_df, ey_df


def test_synthetic_lag_45min():
    """
    US-2 Independent Test: Verify the pipeline reports 45 min (±1 min) as optimal lag.
    """
    # 1. Generate synthetic data with known true lag
    true_lag = 45
    vsw_df, ey_df = generate_synthetic_dataset(true_lag_minutes=true_lag)
    
    # 2. Run the lag search
    optimal_lag, max_corr, lag_values, corr_values = find_optimal_lag(
        vsw_df, ey_df, 
        min_lag=LAG_WINDOW_MIN, 
        max_lag=LAG_WINDOW_MAX, 
        step=LAG_STEP
    )
    
    # 3. Verify the optimal lag is within ±1 minute of the true lag
    assert abs(optimal_lag - true_lag) <= 1, (
        f"Optimal lag {optimal_lag} min is outside tolerance of true lag {true_lag} min. "
        f"Difference: {abs(optimal_lag - true_lag)} min"
    )
    
    # 4. Verify the correlation at optimal lag is positive and significant
    assert max_corr > 0, "Correlation at optimal lag should be positive"
    
    # 5. Log results for verification
    print(f"True Lag: {true_lag} min")
    print(f"Optimal Lag Found: {optimal_lag} min")
    print(f"Max Correlation: {max_corr:.4f}")
    print(f"Lag Difference: {abs(optimal_lag - true_lag)} min")
    
    # Assert the difference is exactly within tolerance
    assert abs(optimal_lag - true_lag) <= 1

if __name__ == "__main__":
    test_synthetic_lag_45min()
    print("Test passed: Synthetic lag detection works correctly.")
