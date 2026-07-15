import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path

# Import the functions to test
from sensitivity_analysis import (
    run_sensitivity_analysis,
    generate_sensitivity_table,
    load_analysis_results
)

@pytest.fixture
def mock_analysis_results():
    """Create mock correlation results for testing."""
    data = {
        'channel': ['Fp1', 'Fp2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2'],
        'correlation': [0.65, 0.45, -0.32, 0.78, 0.12, -0.55, 0.82, 0.23, -0.15, 0.67],
        'p_value': [0.001, 0.03, 0.08, 0.0001, 0.45, 0.02, 0.0005, 0.15, 0.25, 0.002],
        'method': ['pearson'] * 10,
        'adjusted_p_value': [0.005, 0.12, 0.18, 0.0004, 0.90, 0.08, 0.002, 0.35, 0.50, 0.01]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_results_file(mock_analysis_results):
    """Create a temporary CSV file with mock results."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        mock_analysis_results.to_csv(f, index=False)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)

def test_run_sensitivity_analysis_at_0_05(mock_analysis_results):
    """Test sensitivity analysis at p <= 0.05 threshold."""
    result = run_sensitivity_analysis(mock_analysis_results, thresholds=[0.05])
    
    assert len(result) == 1
    assert result.iloc[0]['threshold'] == 0.05
    
    # At p <= 0.05 (raw), we expect: Fp1(0.001), Fp2(0.03), F4(0.0001), C4(0.02), P3(0.0005), O2(0.002)
    # At p <= 0.05 (adjusted), we expect: Fp1(0.005), F4(0.0004), P3(0.002), O2(0.01)
    # Union should include: Fp1, Fp2, F4, C4, P3, O2
    assert result.iloc[0]['significant_count_raw'] == 6
    assert result.iloc[0]['significant_count_adjusted'] == 4
    assert result.iloc[0]['unique_significant_channels'] == 6
    assert set(result.iloc[0]['channels']) == {'Fp1', 'Fp2', 'F4', 'C4', 'P3', 'O2'}

def test_run_sensitivity_analysis_at_0_01(mock_analysis_results):
    """Test sensitivity analysis at p <= 0.01 threshold."""
    result = run_sensitivity_analysis(mock_analysis_results, thresholds=[0.01])
    
    assert len(result) == 1
    assert result.iloc[0]['threshold'] == 0.01
    
    # At p <= 0.01 (raw): Fp1(0.001), F4(0.0001), P3(0.0005), O2(0.002)
    # At p <= 0.01 (adjusted): Fp1(0.005), F4(0.0004), P3(0.002), O2(0.01)
    assert result.iloc[0]['significant_count_raw'] == 4
    assert result.iloc[0]['significant_count_adjusted'] == 4
    assert result.iloc[0]['unique_significant_channels'] == 4
    assert set(result.iloc[0]['channels']) == {'Fp1', 'F4', 'P3', 'O2'}

def test_run_sensitivity_analysis_multiple_thresholds(mock_analysis_results):
    """Test sensitivity analysis with multiple thresholds."""
    result = run_sensitivity_analysis(mock_analysis_results, thresholds=[0.05, 0.01])
    
    assert len(result) == 2
    assert result.iloc[0]['threshold'] == 0.05
    assert result.iloc[1]['threshold'] == 0.01
    
    # More channels should be significant at 0.05 than at 0.01
    assert result.iloc[0]['unique_significant_channels'] > result.iloc[1]['unique_significant_channels']

def test_generate_sensitivity_table(mock_analysis_results, temp_results_file):
    """Test generation of sensitivity table CSV."""
    # Temporarily override the load function to use our temp file
    import sensitivity_analysis
    original_load = sensitivity_analysis.load_analysis_results
    
    def mock_load(path):
        return pd.read_csv(temp_results_file)
    
    sensitivity_analysis.load_analysis_results = mock_load
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test_sensitivity_table.csv')
            
            # Run the full pipeline
            results_df = load_analysis_results(temp_results_file)
            sensitivity_df = run_sensitivity_analysis(results_df, [0.05, 0.01])
            table_df = generate_sensitivity_table(sensitivity_df, output_path)
            
            # Verify file exists
            assert os.path.exists(output_path)
            
            # Verify content
            saved_df = pd.read_csv(output_path)
            assert len(saved_df) == 2
            assert 'p_threshold' in saved_df.columns
            assert 'channels' in saved_df.columns
            
            # Verify the 0.05 threshold row
            row_05 = saved_df[saved_df['p_threshold'] == 0.05].iloc[0]
            assert row_05['significant_channels_raw'] == 6
            assert row_05['unique_significant_channels'] == 6
    finally:
        sensitivity_analysis.load_analysis_results = original_load

def test_empty_results():
    """Test sensitivity analysis with empty dataframe."""
    empty_df = pd.DataFrame(columns=['channel', 'correlation', 'p_value', 'method', 'adjusted_p_value'])
    result = run_sensitivity_analysis(empty_df, thresholds=[0.05])
    
    assert len(result) == 1
    assert result.iloc[0]['significant_count_raw'] == 0
    assert result.iloc[0]['significant_count_adjusted'] == 0
    assert result.iloc[0]['unique_significant_channels'] == 0
    assert result.iloc[0]['proportion_significant'] == 0.0
