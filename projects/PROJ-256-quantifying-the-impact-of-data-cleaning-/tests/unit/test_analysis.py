import pytest
import pandas as pd
import numpy as np
import os
import json
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from analysis import run_t_test, run_linear_regression, analyze_dataset, run_baseline_analysis

def test_run_t_test_valid_data():
    data = {
        'group': ['A', 'A', 'B', 'B', 'A', 'B'],
        'outcome': [10.0, 11.0, 12.0, 13.0, 10.5, 12.5]
    }
    df = pd.DataFrame(data)
    result = run_t_test(df, 'group', 'outcome')
    assert 'p_value' in result
    assert 'ci_95' in result
    assert 'effect_size_cohen_d' in result
    # Basic validation
    assert 0 < result['p_value'] < 1
    assert np.isfinite(result['ci_95'][0]) and np.isfinite(result['ci_95'][1])

def test_run_linear_regression_valid_data():
    data = {
        'predictor': [1.0, 2.0, 3.0, 4.0, 5.0],
        'outcome': [2.0, 4.0, 5.0, 4.0, 5.0]
    }
    df = pd.DataFrame(data)
    result = run_linear_regression(df, 'predictor', 'outcome')
    assert 'p_value' in result
    assert 'r_squared' in result
    assert 'ci_95' in result
    assert 0 < result['p_value'] < 1
    assert np.isfinite(result['ci_95'][0]) and np.isfinite(result['ci_95'][1])

def test_analyze_dataset():
    data = {
        'group': ['A', 'A', 'B', 'B', 'A', 'B'] * 10,
        'outcome': [10.0, 11.0, 12.0, 13.0, 10.5, 12.5] * 10,
        'feature_a': np.random.randn(60)
    }
    df = pd.DataFrame(data)
    result = analyze_dataset(df, 'test_dataset')
    assert result['dataset_name'] == 'test_dataset'
    assert 't_tests' in result
    assert 'regressions' in result
    # Check that p-values are valid if tests were run
    for test in result['t_tests']:
        if test:
            assert 0 < test['p_value'] < 1
    for reg in result['regressions']:
        if reg:
            assert 0 < reg['p_value'] < 1

def test_run_baseline_analysis_dataframe_input(tmp_path):
    data = {
        'group': ['A', 'B'] * 10,
        'outcome': [10.0, 12.0] * 10
    }
    df = pd.DataFrame(data)
    result = run_baseline_analysis(df, dataset_name='inline_test')
    assert result is not None
    assert result['dataset_name'] == 'inline_test'
    assert 't_tests' in result

def test_run_baseline_analysis_dir_input(tmp_path):
    # Create a dummy CSV
    csv_path = tmp_path / "test.csv"
    data = {
        'group': ['A', 'B'] * 10,
        'outcome': [10.0, 12.0] * 10
    }
    pd.DataFrame(data).to_csv(csv_path, index=False)

    output_file = tmp_path / "output.json"
    result = run_baseline_analysis(str(tmp_path), str(output_file))
    assert result is True
    assert output_file.exists()
    with open(output_file) as f:
        data = json.load(f)
    assert len(data) >= 1
    assert 't_tests' in data[0]