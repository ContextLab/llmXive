"""
Unit tests for sensitivity analysis module.
"""

import os
import tempfile
import json
import pytest
import pandas as pd
import numpy as np

from code.sensitivity_analysis import (
    load_coverage_results,
    run_sensitivity_analysis,
    load_config
)

def test_load_coverage_results_with_deviation():
    """Test loading a CSV that already has a deviation column."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df = pd.DataFrame({
            'series_id': [1, 2, 3],
            'model': ['A', 'B', 'C'],
            'horizon': [1, 2, 3],
            'nominal_coverage': [0.95, 0.95, 0.80],
            'empirical_coverage': [0.90, 0.95, 0.75],
            'deviation': [0.05, 0.00, 0.05]
        })
        df.to_csv(f.name, index=False)
        temp_path = f.name

    try:
        result = load_coverage_results(temp_path)
        assert 'deviation' in result.columns
        assert len(result) == 3
        # Check if deviation is correctly used (not recalculated if present)
        pd.testing.assert_series_equal(result['deviation'], df['deviation'])
    finally:
        os.unlink(temp_path)

def test_load_coverage_results_calculates_deviation():
    """Test loading a CSV that calculates deviation from nominal and empirical."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        df = pd.DataFrame({
            'series_id': [1, 2, 3],
            'model': ['A', 'B', 'C'],
            'horizon': [1, 2, 3],
            'nominal_coverage': [0.95, 0.95, 0.80],
            'empirical_coverage': [0.90, 0.95, 0.75]
            # No deviation column
        })
        df.to_csv(f.name, index=False)
        temp_path = f.name

    try:
        result = load_coverage_results(temp_path)
        assert 'deviation' in result.columns
        # Expected deviations: |0.95-0.90|=0.05, |0.95-0.95|=0.00, |0.80-0.75|=0.05
        expected = [0.05, 0.00, 0.05]
        assert list(result['deviation']) == expected
    finally:
        os.unlink(temp_path)

def test_run_sensitivity_analysis():
    """Test the sensitivity analysis logic."""
    df = pd.DataFrame({
        'series_id': list(range(10)),
        'model': ['A'] * 10,
        'horizon': [1] * 10,
        'deviation': [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
    })

    sensitivity_range = [0.00, 0.10]
    threshold_step = 0.02

    result = run_sensitivity_analysis(df, sensitivity_range, threshold_step)

    assert 'threshold' in result.columns
    assert 'count_within_threshold' in result.columns
    assert 'percentage' in result.columns

    # Check specific thresholds
    # At 0.02: count should be 2 (0.01, 0.02)
    row_0_02 = result[result['threshold'] == 0.02]
    assert len(row_0_02) == 1
    assert row_0_02['count_within_threshold'].values[0] == 2

    # At 0.10: count should be 10 (all)
    row_0_10 = result[result['threshold'] == 0.10]
    assert len(row_0_10) == 1
    assert row_0_10['count_within_threshold'].values[0] == 10

def test_run_sensitivity_analysis_empty_df():
    """Test sensitivity analysis with empty dataframe."""
    df = pd.DataFrame(columns=['series_id', 'model', 'horizon', 'deviation'])
    sensitivity_range = [0.0, 0.1]

    result = run_sensitivity_analysis(df, sensitivity_range)

    assert len(result) == 0
    assert 'threshold' in result.columns

def test_load_config():
    """Test loading a temporary config file."""
    config_data = {
        'sensitivity_range': [0.01, 0.05],
        'nominal_levels': [0.80, 0.95]
    }

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
        import yaml
        yaml.dump(config_data, f)
        temp_path = f.name

    try:
        config = load_config(temp_path)
        assert config['sensitivity_range'] == [0.01, 0.05]
        assert config['nominal_levels'] == [0.80, 0.95]
    finally:
        os.unlink(temp_path)