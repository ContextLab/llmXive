"""
Unit tests for sensitivity analysis module (T027).
"""

import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.sensitivity import (
    load_signals,
    load_cleaned_data,
    filter_data_for_baseline,
    calculate_metrics_for_soc,
    run_sensitivity_analysis
)


@pytest.fixture
def sample_data():
    """Create sample cleaned VAERS data for testing."""
    data = {
        'VAX_TYPE': ['COVID-19', 'COVID-19', 'Influenza', 'Influenza', 'Pneumococcal', 'Pneumococcal'],
        'SOC': ['SOC_A', 'SOC_B', 'SOC_A', 'SOC_C', 'SOC_B', 'SOC_D'],
        'REPT_DATE': pd.date_range('2020-01-01', periods=6)
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_signals():
    """Create sample signals DataFrame for testing."""
    data = {
        'soc': ['SOC_A', 'SOC_B'],
        'ror': [2.5, 1.8],
        'ror_ci_lower': [1.2, 0.9],
        'ror_ci_upper': [4.1, 3.5],
        'prr': [2.2, 1.6],
        'prr_ci_lower': [1.1, 0.8],
        'prr_ci_upper': [3.9, 3.2],
        'ic': [0.8, 0.4],
        'ic_ci_lower': [0.1, -0.2],
        'ic_ci_upper': [1.5, 1.0],
        'signal_flag': [True, True],
        'p_adj': [0.01, 0.03]
    }
    return pd.DataFrame(data)


def test_filter_data_for_baseline_primary(sample_data):
    """Test filtering for primary baseline (Non-COVID, Non-Flu)."""
    filtered = filter_data_for_baseline(sample_data, 'primary')

    # Should contain COVID-19 and Pneumococcal (Non-Flu)
    expected_vax_types = {'COVID-19', 'Pneumococcal'}
    assert set(filtered['VAX_TYPE'].unique()) == expected_vax_types
    assert len(filtered) == 4  # 2 COVID + 2 Pneumococcal


def test_filter_data_for_baseline_flu_only(sample_data):
    """Test filtering for flu-only baseline."""
    filtered = filter_data_for_baseline(sample_data, 'flu_only')

    # Should contain COVID-19 and Influenza
    expected_vax_types = {'COVID-19', 'Influenza'}
    assert set(filtered['VAX_TYPE'].unique()) == expected_vax_types
    assert len(filtered) == 4  # 2 COVID + 2 Influenza


def test_calculate_metrics_for_soc(sample_data):
    """Test metric calculation for a specific SOC."""
    # Create a larger dataset to meet minimum report requirement
    data = {
        'VAX_TYPE': ['COVID-19'] * 10 + ['Influenza'] * 10,
        'SOC': ['SOC_A'] * 5 + ['SOC_B'] * 5 + ['SOC_A'] * 3 + ['SOC_C'] * 7
    }
    df = pd.DataFrame(data)

    metrics = calculate_metrics_for_soc(df, 'SOC_A')

    assert metrics is not None
    assert 'ror' in metrics
    assert 'prr' in metrics
    assert 'ic' in metrics
    assert metrics['covid_events'] == 5
    assert metrics['baseline_events'] == 3
    assert metrics['total_reports'] == 8


def test_calculate_metrics_insufficient_data(sample_data):
    """Test that metrics return None when insufficient data."""
    # This sample_data has too few reports for any SOC
    metrics = calculate_metrics_for_soc(sample_data, 'SOC_A')
    assert metrics is None


def test_run_sensitivity_analysis_with_empty_signals(tmp_path):
    """Test sensitivity analysis with no signals."""
    signals_df = pd.DataFrame(columns=['soc', 'ror', 'signal_flag'])
    cleaned_df = pd.DataFrame({
        'VAX_TYPE': ['COVID-19', 'Influenza'],
        'SOC': ['SOC_A', 'SOC_A']
    })

    output_path = tmp_path / 'sensitivity_analysis.csv'
    result = run_sensitivity_analysis(signals_df, cleaned_df, str(output_path))

    assert len(result) == 0
    assert output_path.exists()


def test_run_sensitivity_analysis_full(tmp_path, sample_signals):
    """Test full sensitivity analysis workflow."""
    # Create realistic sample data with enough reports
    np.random.seed(42)
    n_covid = 100
    n_flu = 100
    n_other = 100

    data = {
        'VAX_TYPE': (
            ['COVID-19'] * n_covid +
            ['Influenza'] * n_flu +
            ['Pneumococcal'] * n_other
        ),
        'SOC': (
            ['SOC_A'] * 30 + ['SOC_B'] * 20 + ['SOC_C'] * 50 +  # COVID
            ['SOC_A'] * 10 + ['SOC_B'] * 40 + ['SOC_C'] * 50 +  # Flu
            ['SOC_A'] * 5 + ['SOC_B'] * 15 + ['SOC_C'] * 80     # Other
        )
    }
    cleaned_df = pd.DataFrame(data)

    output_path = tmp_path / 'sensitivity_analysis.csv'
    result = run_sensitivity_analysis(sample_signals, cleaned_df, str(output_path))

    assert len(result) > 0
    assert 'soc' in result.columns
    assert 'ror_delta' in result.columns
    assert 'prr_delta' in result.columns
    assert 'ic_delta' in result.columns
    assert 'baseline_type' in result.columns
    assert output_path.exists()
