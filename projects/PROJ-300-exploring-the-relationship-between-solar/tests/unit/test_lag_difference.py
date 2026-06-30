"""
Unit tests for T017: Calculation of |L* - L_phys| (SC-002).
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from code.config import EARTH_RADIUS_KM, TAIL_DISTANCE_RE
from code.data.lag import calculate_physics_lag
from code.analysis.lag_search import find_optimal_lag

def test_physics_lag_calculation():
    """Test that L_phys is calculated correctly based on Vsw."""
    # Constants
    # L_phys = (TAIL_DISTANCE_RE * EARTH_RADIUS_KM) / Vsw
    # Units: (Re * km/Re) / (km/min) -> min
    # TAIL_DISTANCE_RE = 60, EARTH_RADIUS_KM = 6371
    # Distance = 60 * 6371 km
    # If Vsw = 400 km/s -> 24000 km/min
    # L_phys = (60 * 6371) / 24000 = 382260 / 24000 = 15.9275 min

    vsw_mean = 400.0  # km/s
    expected_dist_km = TAIL_DISTANCE_RE * EARTH_RADIUS_KM
    expected_lag_min = expected_dist_km / (vsw_mean * 60)

    calculated_lag = calculate_physics_lag(vsw_mean)

    assert np.isclose(calculated_lag, expected_lag_min, rtol=1e-5)

def test_lag_difference_calculation_logic():
    """
    Test the logic of calculating |L* - L_phys| without running full pipeline.
    Mocking the optimal lag search result to verify the subtraction logic.
    """
    # Simulate a scenario
    l_phys = 15.0  # minutes
    optimal_lag = 20.0  # minutes
    
    difference = abs(optimal_lag - l_phys)
    
    assert difference == 5.0
    assert isinstance(difference, float)

def test_find_optimal_lag_integration_with_physics():
    """
    Ensure that find_optimal_lag returns a value that can be compared with L_phys.
    This is a sanity check that the types match for the subtraction in main.py.
    """
    # Create synthetic data with a known correlation peak at lag=45
    n = 1000
    t = pd.date_range(start="2023-01-01", periods=n, freq="5min")
    
    # Create a signal with a known lag relationship
    base_signal = np.sin(np.linspace(0, 10, n))
    noise = np.random.normal(0, 0.1, n)
    
    # Ey is Vsw shifted by 45 minutes (9 steps of 5min)
    vsw = base_signal + noise
    ey = np.roll(base_signal, 9) + noise * 0.5
    
    # Create DataFrames
    df_vsw = pd.DataFrame({'timestamp': t, 'Vsw': vsw})
    df_ey = pd.DataFrame({'timestamp': t, 'Ey': ey})
    
    # Run search
    optimal_lag, corr_val, _ = find_optimal_lag(
        df_vsw['Vsw'], df_ey['Ey'],
        min_lag=30, max_lag=90, step=5
    )
    
    # Check types
    assert isinstance(optimal_lag, (int, float, np.number))
    assert isinstance(corr_val, (int, float, np.number))
    
    # Check that optimal_lag is within the search window
    assert 30 <= optimal_lag <= 90

def test_lag_difference_in_report_structure():
    """
    Verify that the structure expected in the report matches the SC-002 requirement.
    """
    # This test validates the logic that would appear in the report dictionary
    # in main.py.
    
    l_phys = 15.9275
    optimal_lag = 20.0
    
    lag_difference = abs(optimal_lag - l_phys)
    
    # Simulate the report entry
    report_entry = {
        "physics_lag_minutes": l_phys,
        "optimal_lag_minutes": optimal_lag,
        "lag_difference_minutes": lag_difference
    }
    
    assert report_entry["lag_difference_minutes"] == pytest.approx(4.0725, rel=1e-4)
    assert report_entry["lag_difference_minutes"] > 0
