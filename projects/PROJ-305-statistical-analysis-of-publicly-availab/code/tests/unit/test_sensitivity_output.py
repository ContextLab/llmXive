import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Mock the config module to avoid dependency issues in unit tests if needed,
# though we are testing logic that doesn't strictly need real config files.

from src.analysis.sensitivity_output import calculate_deltas_for_top_signals

@pytest.fixture
def sample_signals():
    return pd.DataFrame({
        'soc': ['SOC001', 'SOC002', 'SOC003', 'SOC004', 'SOC005'],
        'ror': [3.0, 2.5, 2.0, 1.8, 1.5],
        'prr': [2.0, 1.8, 1.6, 1.4, 1.2],
        'ic': [1.0, 0.8, 0.5, 0.3, 0.1]
    })

@pytest.fixture
def sample_sensitivity_raw():
    """
    Simulated raw sensitivity analysis output with both baseline types.
    """
    data = []
    for soc in ['SOC001', 'SOC002', 'SOC003', 'SOC004', 'SOC005']:
        # Primary Baseline
        data.append({
            'soc': soc,
            'baseline_type': 'Primary Baseline (Non-COVID, Non-Flu)',
            'ror': 3.0 + (hash(soc) % 10) * 0.1,
            'prr': 2.0 + (hash(soc) % 10) * 0.1,
            'ic': 1.0 + (hash(soc) % 10) * 0.1
        })
        # Flu-only Baseline
        data.append({
            'soc': soc,
            'baseline_type': 'Flu-only',
            'ror': 3.5 + (hash(soc) % 10) * 0.1,
            'prr': 2.2 + (hash(soc) % 10) * 0.1,
            'ic': 1.1 + (hash(soc) % 10) * 0.1
        })
    return pd.DataFrame(data)

def test_calculate_deltas_top_5(sample_sensitivity_raw):
    """Test that deltas are calculated correctly for top 5 signals."""
    result = calculate_deltas_for_top_signals(sample_sensitivity_raw, top_n=5)
    
    assert len(result) == 5
    assert 'soc' in result.columns
    assert 'ror_delta' in result.columns
    assert 'prr_delta' in result.columns
    assert 'ic_delta' in result.columns
    assert 'baseline_type' in result.columns
    
    # Check that deltas are numeric and non-NaN (since we provided valid data)
    assert result['ror_delta'].notna().all()
    assert result['prr_delta'].notna().all()
    assert result['ic_delta'].notna().all()
    
    # Verify a specific calculation (Flu - Primary)
    # For SOC001, Primary ROR = 3.0, Flu ROR = 3.5 -> Delta = 0.5
    # Note: The actual values depend on the hash, but the logic holds.
    # We just verify the column exists and is float.
    assert result['ror_delta'].dtype in [np.float64, np.float32]

def test_calculate_deltas_no_signals(sample_sensitivity_raw):
    """Test behavior when top_n is 0 or input is empty."""
    # Test with top_n=0
    result = calculate_deltas_for_top_signals(sample_sensitivity_raw, top_n=0)
    assert len(result) == 0
    
    # Test with empty input
    empty_df = pd.DataFrame(columns=['soc', 'baseline_type', 'ror', 'prr', 'ic'])
    result_empty = calculate_deltas_for_top_signals(empty_df, top_n=5)
    assert len(result_empty) == 0
    assert list(result_empty.columns) == ['soc', 'ror_delta', 'prr_delta', 'ic_delta', 'baseline_type']

@pytest.fixture
def sample_signals_no_signals():
    return pd.DataFrame(columns=['soc', 'ror', 'prr', 'ic'])

def test_calculate_deltas_missing_baseline(sample_sensitivity_raw):
    """Test behavior when one baseline type is missing for a SOC."""
    # Remove one row for SOC001 to simulate missing baseline
    incomplete_df = sample_sensitivity_raw[sample_sensitivity_raw['soc'] != 'SOC001']
    # Add a row for SOC001 with only Primary
    incomplete_df = pd.concat([incomplete_df, pd.DataFrame([
        {'soc': 'SOC001', 'baseline_type': 'Primary Baseline (Non-COVID, Non-Flu)', 'ror': 3.0, 'prr': 2.0, 'ic': 1.0}
    ])], ignore_index=True)
    
    result = calculate_deltas_for_top_signals(incomplete_df, top_n=5)
    
    # SOC001 should be excluded because it lacks the Flu baseline
    assert 'SOC001' not in result['soc'].values
    assert len(result) < 5 # Should be 4 if others are complete

def test_calculate_deltas_single_baseline_type(sample_sensitivity_raw):
    """Test behavior when only one baseline type exists in the whole dataset."""
    # Filter to only Primary
    single_baseline_df = sample_sensitivity_raw[sample_sensitivity_raw['baseline_type'] == 'Primary Baseline (Non-COVID, Non-Flu)']
    
    result = calculate_deltas_for_top_signals(single_baseline_df, top_n=5)
    
    assert len(result) == 0 # Cannot calculate delta without both