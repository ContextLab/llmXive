"""
Unit tests for T017: Calculation of |L* - L_phys| in main.py
"""
import pytest
import json
import os
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Mock the heavy imports to isolate the logic test
@pytest.fixture
def mock_dependencies():
    with patch('code.main.fetch_omni_sw') as mock_omni, \
         patch('code.main.fetch_themis_ey') as mock_themis, \
         patch('code.main.clean_and_resample') as mock_clean, \
         patch('code.main.calculate_physics_lag') as mock_calc_lag, \
         patch('code.main.find_optimal_lag') as mock_find_lag, \
         patch('code.main.apply_lag_shift') as mock_apply_lag, \
         patch('code.main.calculate_correlation') as mock_corr, \
         patch('code.main.circular_block_permutation') as mock_perm, \
         patch('code.main.analyze_thresholds') as mock_sens, \
         patch('code.main.plot_scatter'), \
         patch('code.main.plot_timeseries'):
         
         # Setup mock data
         df_vsw = pd.DataFrame({
             'timestamp': pd.date_range('2023-01-01', periods=100, freq='5T'),
             'Vsw': np.random.uniform(400, 600, 100)
         })
         df_ey = pd.DataFrame({
             'timestamp': df_vsw['timestamp'],
             'Ey': np.random.uniform(-1, 1, 100)
         })
         
         mock_omni.return_value = df_vsw
         mock_themis.return_value = df_ey
         mock_clean.return_value = (df_vsw, df_ey)
         
         # T017 Specific: Mock L_phys and L*
         mock_calc_lag.return_value = 45.0  # L_phys = 45
         mock_find_lag.return_value = {
             'optimal_lag': 50,  # L* = 50
             'max_correlation': 0.8
         }
         
         mock_apply_lag.return_value = df_vsw
         mock_corr.return_value = (0.8, 0.01)
         mock_perm.return_value = (0.01, True)
         mock_sens.return_value = {"400": 0.5, "500": 0.6, "600": 0.7}
         
         yield {
             'mock_calc_lag': mock_calc_lag,
             'mock_find_lag': mock_find_lag,
             'mock_perm': mock_perm
         }

def test_t017_lag_difference_calculation(mock_dependencies):
    """
    Verifies that main.py calculates |L* - L_phys| correctly and includes it in the report.
    SC-002 Requirement.
    """
    from code.main import run_pipeline
    
    # Run the pipeline
    report = run_pipeline("2023-01-01", "2023-01-02")
    
    # Verify L_phys and L* were used
    mock_dependencies['mock_calc_lag'].assert_called_once()
    mock_dependencies['mock_find_lag'].assert_called_once()
    
    # Verify the calculation: |50 - 45| = 5
    assert 'lags' in report
    assert 'lag_difference_minutes' in report['lags']
    
    expected_diff = abs(50 - 45)
    actual_diff = report['lags']['lag_difference_minutes']
    
    assert actual_diff == expected_diff, f"Expected |L* - L_phys| to be {expected_diff}, got {actual_diff}"
    
    # Verify the value is numeric
    assert isinstance(actual_diff, (int, float))

def test_t017_report_structure(mock_dependencies):
    """
    Ensures the report structure includes the new lag_difference key.
    """
    from code.main import run_pipeline
    
    report = run_pipeline("2023-01-01", "2023-01-02")
    
    # Check top-level keys
    assert 'metadata' in report
    assert 'lags' in report
    assert 'correlations' in report
    assert 'sensitivity_table' in report
    
    # Check specific T017 key
    assert 'L_phys_minutes' in report['lags']
    assert 'L_star_minutes' in report['lags']
    assert 'lag_difference_minutes' in report['lags']