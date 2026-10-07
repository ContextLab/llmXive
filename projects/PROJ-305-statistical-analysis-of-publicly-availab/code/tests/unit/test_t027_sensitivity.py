"""
Unit tests for T027 sensitivity analysis.

Tests the sensitivity analysis module that compares different baseline groups
for top signals.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.sensitivity import (
    load_signals,
    load_cleaned_data,
    filter_data_for_baseline,
    calculate_metrics_for_soc,
    run_sensitivity_analysis
)

@pytest.fixture
def sample_cleaned_data():
    """Create sample cleaned data for testing."""
    data = {
        'VAX_TYPE': [
            'COVID-19', 'COVID-19', 'COVID-19',
            'Influenza', 'Influenza', 'Influenza',
            'Other Vaccine', 'Other Vaccine', 'Other Vaccine'
        ],
        'SOC': [
            'SOC001', 'SOC002', 'SOC001',
            'SOC001', 'SOC002', 'SOC003',
            'SOC001', 'SOC002', 'SOC003'
        ],
        'REPT_DATE': pd.date_range('2020-01-01', periods=9),
        'AGE': [30, 40, 50, 35, 45, 55, 25, 35, 45]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_signals():
    """Create sample signals DataFrame for testing."""
    data = {
        'soc': ['SOC001', 'SOC002', 'SOC003'],
        'ror': [2.5, 1.8, 3.0],
        'ror_ci_lower': [1.5, 1.0, 2.0],
        'ror_ci_upper': [3.5, 2.6, 4.0],
        'prr': [2.2, 1.6, 2.8],
        'prr_ci_lower': [1.2, 0.9, 1.8],
        'prr_ci_upper': [3.2, 2.3, 3.8],
        'ic': [0.8, 0.4, 1.2],
        'ic_ci_lower': [0.2, -0.1, 0.5],
        'ic_ci_upper': [1.4, 0.9, 1.9],
        'signal_flag': [True, False, True]
    }
    return pd.DataFrame(data)

def test_load_signals_valid_file(tmp_path):
    """Test loading signals from a valid file."""
    signals_data = {
        'soc': ['SOC001'],
        'ror': [2.5],
        'ror_ci_lower': [1.5],
        'ror_ci_upper': [3.5],
        'prr': [2.2],
        'prr_ci_lower': [1.2],
        'prr_ci_upper': [3.2],
        'ic': [0.8],
        'ic_ci_lower': [0.2],
        'ic_ci_upper': [1.4],
        'signal_flag': [True]
    }
    df = pd.DataFrame(signals_data)
    signals_path = tmp_path / 'signals.csv'
    df.to_csv(signals_path, index=False)
    
    loaded = load_signals(str(signals_path))
    assert len(loaded) == 1
    assert 'soc' in loaded.columns
    assert 'signal_flag' in loaded.columns

def test_load_signals_missing_file():
    """Test that loading from non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        load_signals('/nonexistent/path/signals.csv')

def test_filter_data_for_baseline_primary(sample_cleaned_data):
    """Test filtering for Full Non-COVID baseline."""
    filtered = filter_data_for_baseline(sample_cleaned_data, 'full_non_covid')
    # Should exclude COVID-19 rows (3 rows), keep 6
    assert len(filtered) == 6
    assert not filtered['VAX_TYPE'].str.contains('COVID-19').any()

def test_filter_data_for_baseline_flu_only(sample_cleaned_data):
    """Test filtering for Flu-only baseline."""
    filtered = filter_data_for_baseline(sample_cleaned_data, 'flu_only')
    # Should only keep Influenza rows (3 rows)
    assert len(filtered) == 3
    assert filtered['VAX_TYPE'].str.contains('Influenza').all()

def test_calculate_metrics_for_soc(sample_cleaned_data):
    """Test metric calculation for a specific SOC."""
    covid_data = sample_cleaned_data[sample_cleaned_data['VAX_TYPE'].str.contains('COVID-19')]
    baseline_data = sample_cleaned_data[~sample_cleaned_data['VAX_TYPE'].str.contains('COVID-19')]
    
    metrics = calculate_metrics_for_soc('SOC001', covid_data, baseline_data)
    
    assert metrics is not None
    assert 'ror' in metrics
    assert 'prr' in metrics
    assert 'ic' in metrics
    assert 'ror_ci_lower' in metrics
    assert 'ror_ci_upper' in metrics

def test_calculate_metrics_insufficient_data(sample_cleaned_data):
    """Test that insufficient data returns None."""
    covid_data = sample_cleaned_data[sample_cleaned_data['VAX_TYPE'].str.contains('COVID-19')]
    baseline_data = sample_cleaned_data[~sample_cleaned_data['VAX_TYPE'].str.contains('COVID-19')]
    
    # SOC004 doesn't exist, should return None
    metrics = calculate_metrics_for_soc('SOC004', covid_data, baseline_data)
    assert metrics is None

def test_run_sensitivity_analysis_with_empty_signals(sample_cleaned_data):
    """Test sensitivity analysis with no signals."""
    empty_signals = pd.DataFrame(columns=['soc', 'ror', 'prr', 'ic', 'signal_flag'])
    
    covid_data = sample_cleaned_data[sample_cleaned_data['VAX_TYPE'].str.contains('COVID-19')]
    baseline_full = sample_cleaned_data[~sample_cleaned_data['VAX_TYPE'].str.contains('COVID-19')]
    baseline_flu = sample_cleaned_data[sample_cleaned_data['VAX_TYPE'].str.contains('Influenza')]
    baseline_non_flu = sample_cleaned_data[
        ~sample_cleaned_data['VAX_TYPE'].str.contains('COVID-19') & 
        ~sample_cleaned_data['VAX_TYPE'].str.contains('Influenza')
    ]
    
    results = run_sensitivity_analysis(
        signals_df=empty_signals,
        covid_data=covid_data,
        baseline_full=baseline_full,
        baseline_flu=baseline_flu,
        baseline_non_flu=baseline_non_flu,
        top_n=5
    )
    
    assert results.empty

def test_run_sensitivity_analysis_full(sample_cleaned_data, sample_signals):
    """Test full sensitivity analysis workflow."""
    covid_data = sample_cleaned_data[sample_cleaned_data['VAX_TYPE'].str.contains('COVID-19')]
    baseline_full = sample_cleaned_data[~sample_cleaned_data['VAX_TYPE'].str.contains('COVID-19')]
    baseline_flu = sample_cleaned_data[sample_cleaned_data['VAX_TYPE'].str.contains('Influenza')]
    baseline_non_flu = sample_cleaned_data[
        ~sample_cleaned_data['VAX_TYPE'].str.contains('COVID-19') & 
        ~sample_cleaned_data['VAX_TYPE'].str.contains('Influenza')
    ]
    
    results = run_sensitivity_analysis(
        signals_df=sample_signals,
        covid_data=covid_data,
        baseline_full=baseline_full,
        baseline_flu=baseline_flu,
        baseline_non_flu=baseline_non_flu,
        top_n=5
    )
    
    # Should have results for SOC001 and SOC003 (the ones with signal_flag=True)
    # Each SOC can have up to 2 baseline comparisons (flu_only and non_covid_non_flu)
    assert len(results) <= 4  # 2 signals * 2 baselines
    assert 'soc' in results.columns
    assert 'ror_delta' in results.columns
    assert 'prr_delta' in results.columns
    assert 'ic_delta' in results.columns
    assert 'baseline_type' in results.columns
    assert results['baseline_type'].isin(['flu_only', 'non_covid_non_flu']).all()