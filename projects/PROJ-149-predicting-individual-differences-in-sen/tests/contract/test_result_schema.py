"""
tests/contract/test_result_schema.py
Validates schemas of model_results.json, correlations_corrected.csv, etc.
"""
import pytest
import pandas as pd
import json
from pathlib import Path

RESULTS_PATH = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'model_results.json'
CORR_PATH = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'correlations_corrected.csv'
NONLIN_PATH = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'non_linear_comparison.json'
PERM_PATH = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'permutation_results.json'

def test_model_results_schema():
    if not RESULTS_PATH.exists():
        pytest.skip("File not found")
    with open(RESULTS_PATH) as f:
        data = json.load(f)
    required_keys = ['adjusted_r2', 'optimal_lambda', 'rmse', 'test_r2', 'test_rmse']
    for k in required_keys:
        assert k in data, f"Missing key in model_results: {k}"

def test_correlations_corrected_schema():
    if not CORR_PATH.exists():
        pytest.skip("File not found")
    df = pd.read_csv(CORR_PATH)
    required_cols = ['band', 'r_value', 'p_value', 'n', 'significant']
    for c in required_cols:
        assert c in df.columns, f"Missing column in correlations_corrected: {c}"

def test_non_linear_comparison_schema():
    if not NONLIN_PATH.exists():
        pytest.skip("File not found")
    with open(NONLIN_PATH) as f:
        data = json.load(f)
    assert 'significant_at_0p05' in data
    assert 'interpretation' in data

def test_permutation_results_schema():
    if not PERM_PATH.exists():
        pytest.skip("File not found")
    with open(PERM_PATH) as f:
        data = json.load(f)
    assert 'observed_r2' in data
    assert 'p_value' in data