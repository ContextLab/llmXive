"""
Unit tests for T027 Sensitivity Analysis Module
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.analysis.sensitivity import (
    load_signals,
    load_cleaned_data,
    filter_data_for_baseline,
    calculate_metrics_for_soc,
    run_sensitivity_analysis
)

@pytest.fixture
def sample_signals():
    """Create sample signals DataFrame for testing."""
    data = {
        'soc': ['SOC001', 'SOC002', 'SOC003', 'SOC004', 'SOC005', 'SOC006'],
        'ror': [3.5, 2.8, 1.9, 4.2, 2.1, 1.5],
        'ror_ci_lower': [2.1, 1.8, 0.9, 3.0, 1.2, 0.8],
        'ror_ci_upper': [5.8, 4.3, 3.5, 6.1, 3.8, 2.9],
        'prr': [2.9, 2.3, 1.6, 3.5, 1.8, 1.3],
        'prr_ci_lower': [1.8, 1.5, 0.8, 2.6, 1.1, 0.7],
        'prr_ci_upper': [4.7, 3.5, 2.9, 4.8, 2.9, 2.4],
        'ic': [1.8, 1.4, 0.7, 2.1, 1.1, 0.5],
        'ic_ci_lower': [0.9, 0.6, 0.1, 1.5, 0.4, -0.2],
        'ic_ci_upper': [2.7, 2.2, 1.3, 2.7, 1.8, 1.2],
        'signal_flag': [True, True, False, True, True, False]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_cleaned_data():
    """Create sample cleaned data for testing."""
    # Create a realistic mix of COVID-19 and baseline data
    n_rows = 1000
    np.random.seed(42)
    
    data = {
        'VAX_TYPE': np.random.choice(
            ['COVID-19', 'Influenza', 'MMR', 'Tetanus', 'Hepatitis B'],
            n_rows,
            p=[0.3, 0.2, 0.2, 0.15, 0.15]
        ),
        'SOC': np.random.choice(['SOC001', 'SOC002', 'SOC003', 'SOC004', 'SOC005'], n_rows),
        'baseline_type': ['COVID-19'] * n_rows  # Will be overwritten below
    }
    
    df = pd.DataFrame(data)
    
    # Set baseline_type correctly
    df['baseline_type'] = df.apply(
        lambda row: 'Non-COVID' if 'COVID-19' not in row['VAX_TYPE'] else 'COVID-19',
        axis=1
    )
    
    # Mark Flu-only
    df.loc[df['VAX_TYPE'] == 'Influenza', 'baseline_type'] = 'Flu-only'
    
    return df

def test_load_signals_valid_file(sample_signals):
    """Test loading signals from a valid file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_signals.to_csv(f.name, index=False)
        temp_path = f.name
    
    try:
        loaded = load_signals(temp_path)
        assert len(loaded) == 4  # Only 4 signals (signal_flag == True)
        assert 'soc' in loaded.columns
        assert 'ror' in loaded.columns
    finally:
        os.unlink(temp_path)

def test_load_signals_missing_file():
    """Test that loading from missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_signals('/nonexistent/path/signals.csv')

def test_load_signals_no_signals(sample_signals):
    """Test loading when no signals are present."""
    no_signal_df = sample_signals.copy()
    no_signal_df['signal_flag'] = False
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        no_signal_df.to_csv(f.name, index=False)
        temp_path = f.name
    
    try:
        loaded = load_signals(temp_path)
        assert loaded.empty
    finally:
        os.unlink(temp_path)

def test_filter_data_for_baseline_primary(sample_cleaned_data):
    """Test filtering for Non-COVID (All) baseline."""
    filtered = filter_data_for_baseline(sample_cleaned_data, 'Non-COVID (All)')
    
    # Should include all non-COVID entries (Influenza, MMR, Tetanus, Hepatitis B)
    expected_count = len(sample_cleaned_data[sample_cleaned_data['baseline_type'] == 'Non-COVID'])
    assert len(filtered) == expected_count
    assert not filtered['VAX_TYPE'].str.contains('COVID-19').any()

def test_filter_data_for_baseline_flu_only(sample_cleaned_data):
    """Test filtering for Flu-only baseline."""
    filtered = filter_data_for_baseline(sample_cleaned_data, 'Flu-only')
    
    # Should include only Influenza entries
    expected_count = len(sample_cleaned_data[sample_cleaned_data['baseline_type'] == 'Flu-only'])
    assert len(filtered) == expected_count
    assert all(filtered['VAX_TYPE'] == 'Influenza')

def test_calculate_metrics_for_soc(sample_cleaned_data):
    """Test metric calculation for a specific SOC."""
    metrics = calculate_metrics_for_soc(sample_cleaned_data, 'SOC001')
    
    assert 'ror' in metrics
    assert 'prr' in metrics
    assert 'ic' in metrics
    assert 'ror_ci_lower' in metrics
    assert 'ror_ci_upper' in metrics
    
    # Metrics should be finite (not NaN) if enough data
    if not np.isnan(metrics['ror']):
        assert metrics['ror'] > 0

def test_calculate_metrics_insufficient_data():
    """Test metric calculation with insufficient data."""
    # Create minimal data
    data = pd.DataFrame({
        'VAX_TYPE': ['COVID-19', 'COVID-19', 'Influenza'],
        'SOC': ['SOC001', 'SOC001', 'SOC001'],
        'baseline_type': ['COVID-19', 'COVID-19', 'Flu-only']
    })
    
    metrics = calculate_metrics_for_soc(data, 'SOC001')
    
    # Should return NaN due to insufficient data
    assert np.isnan(metrics['ror'])

def test_run_sensitivity_analysis_with_empty_signals(sample_cleaned_data):
    """Test sensitivity analysis with no signals."""
    empty_signals = pd.DataFrame(columns=['soc', 'ror', 'ror_ci_lower', 'ror_ci_upper',
                                        'prr', 'prr_ci_lower', 'prr_ci_upper',
                                        'ic', 'ic_ci_lower', 'ic_ci_upper', 'signal_flag'])
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        empty_signals.to_csv(f.name, index=False)
        signals_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_cleaned_data.to_csv(f.name, index=False)
        data_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        output_path = f.name
    
    try:
        result = run_sensitivity_analysis(data_path, signals_path, output_path)
        assert result.empty
    finally:
        os.unlink(signals_path)
        os.unlink(data_path)
        os.unlink(output_path)

def test_run_sensitivity_analysis_full(sample_signals, sample_cleaned_data):
    """Test full sensitivity analysis workflow."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_signals.to_csv(f.name, index=False)
        signals_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_cleaned_data.to_csv(f.name, index=False)
        data_path = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        output_path = f.name
    
    try:
        result = run_sensitivity_analysis(data_path, signals_path, output_path)
        
        # Should have results for top 5 signals (or fewer)
        assert len(result) <= 5
        assert 'soc' in result.columns
        assert 'ror_delta' in result.columns
        assert 'prr_delta' in result.columns
        assert 'ic_delta' in result.columns
        assert 'baseline_type' in result.columns
        
        # Verify output file was created
        assert os.path.exists(output_path)
    finally:
        os.unlink(signals_path)
        os.unlink(data_path)
        os.unlink(output_path)