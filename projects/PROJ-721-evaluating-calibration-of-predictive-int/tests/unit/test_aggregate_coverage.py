"""
Unit tests for T019: Aggregate Coverage Results.
"""
import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest
import yaml

# Import the functions we want to test
# We will test the logic by creating mock files and calling main
# Since main() is the entry point, we test the helper functions or mock the file system.

def test_load_config():
    """Test loading configuration."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config = {'nominal_levels': [0.80, 0.95], 'threshold': 0.02}
        yaml.dump(config, f)
        temp_path = f.name

    try:
        from code.aggregate_coverage import load_config
        loaded = load_config(temp_path)
        assert loaded['nominal_levels'] == [0.80, 0.95]
        assert loaded['threshold'] == 0.02
    finally:
        os.unlink(temp_path)

def test_load_coverage_results():
    """Test loading coverage results."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame({
            'series_id': ['S1', 'S2'],
            'model': ['ARIMA', 'ETS'],
            'horizon': [1, 2],
            'empirical_coverage': [0.85, 0.90],
            'level': [0.80, 0.95]
        })
        df.to_csv(f, index=False)
        temp_path = f.name

    try:
        from code.aggregate_coverage import load_coverage_results
        loaded = load_coverage_results(temp_path)
        assert len(loaded) == 2
        assert 'series_id' in loaded.columns
    finally:
        os.unlink(temp_path)

def test_merge_and_calculate():
    """Test merging and deviation calculation."""
    coverage_df = pd.DataFrame({
        'series_id': ['S1'],
        'model': ['ARIMA'],
        'horizon': [1],
        'empirical_coverage': [0.85],
        'level': [0.80]
    })

    pvalues_report = {
        'results': [
            {'model': 'ARIMA', 'horizon': 1, 'p_raw': 0.01, 'p_value': 0.02}
        ]
    }

    nominal_levels = [0.80, 0.95]

    from code.aggregate_coverage import merge_and_calculate
    result = merge_and_calculate(coverage_df, pvalues_report, nominal_levels)

    assert len(result) == 1
    assert result['deviation'].iloc[0] == 0.05
    assert result['nominal_coverage'].iloc[0] == 0.80
    assert 'p_value' in result.columns

def test_full_integration(tmp_path):
    """Test the full flow with temporary files."""
    # Setup temp files
    config_data = {
        'nominal_levels': [0.80, 0.95],
        'threshold': 0.02
    }
    config_file = tmp_path / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)

    coverage_data = pd.DataFrame({
        'series_id': ['S1', 'S2'],
        'model': ['ARIMA', 'ETS'],
        'horizon': [1, 2],
        'empirical_coverage': [0.82, 0.91],
        'level': [0.80, 0.95]
    })
    coverage_file = tmp_path / "coverage_intermediate.csv"
    coverage_data.to_csv(coverage_file, index=False)

    pvalues_data = {
        'results': [
            {'model': 'ARIMA', 'horizon': 1, 'p_raw': 0.05, 'p_value': 0.10},
            {'model': 'ETS', 'horizon': 2, 'p_raw': 0.03, 'p_value': 0.06}
        ]
    }
    pvalues_file = tmp_path / "pvalues.json"
    with open(pvalues_file, 'w') as f:
        json.dump(pvalues_data, f)

    output_file = tmp_path / "coverage.csv"

    # Mock the paths in the module or call a function that takes paths
    # Since main() uses hardcoded paths relative to script, we can't easily test it without changing CWD
    # Instead, we test the logic directly or patch the paths.
    # For this test, we will just verify the logic by calling the helper functions directly.
    # We already tested them above. This test ensures the file I/O works together.
    
    from code.aggregate_coverage import load_config, load_coverage_results, load_pvalues, merge_and_calculate

    config = load_config(str(config_file))
    coverage_df = load_coverage_results(str(coverage_file))
    pvalues_report = load_pvalues(str(pvalues_file))

    final_df = merge_and_calculate(coverage_df, pvalues_report, config['nominal_levels'])

    final_df.to_csv(output_file, index=False)

    assert output_file.exists()
    result_df = pd.read_csv(output_file)
    assert len(result_df) == 2
    assert 'deviation' in result_df.columns
    assert 'p_value' in result_df.columns