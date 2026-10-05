"""
Unit tests for collinearity diagnostics (T024).
"""
import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest

# Import the module under test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))
from collinearity import (
    load_analysis_results,
    calculate_vif,
    run_collinearity_diagnostics,
    save_collinearity_report
)


def test_load_analysis_results():
    """Test merging of complexity and delta data."""
    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        complexity_file = os.path.join(tmpdir, "complexity_metrics.csv")
        delta_file = os.path.join(tmpdir, "delta_scores.csv")

        # Create mock complexity data
        complexity_data = {
            'participant_id': ['P1', 'P1', 'P2', 'P2'],
            'segment_id': ['seg1', 'seg2', 'seg1', 'seg2'],
            'channel': ['Cz', 'Cz', 'Cz', 'Cz'],
            'lzc_value': [0.5, 0.6, 0.7, 0.8],
            'pe_value': [1.0, 1.1, 1.2, 1.3]
        }
        pd.DataFrame(complexity_data).to_csv(complexity_file, index=False)

        # Create mock delta data
        delta_data = {
            'participant_id': ['P1', 'P2'],
            'Fatigue_Delta': [1.5, 2.0],
            'age': [25, 30]
        }
        pd.DataFrame(delta_data).to_csv(delta_file, index=False)

        # Load and merge
        df = load_analysis_results(complexity_file, delta_file)

        assert 'Fatigue_Delta' in df.columns
        assert 'Pre_Complexity' in df.columns
        assert 'age' in df.columns
        assert len(df) == 2


def test_run_collinearity_diagnostics():
    """Test VIF calculation and result structure."""
    # Create mock data with known VIF properties
    np.random.seed(42)
    n = 100
    data = {
        'Fatigue_Delta': np.random.randn(n),
        'Pre_Complexity': np.random.randn(n),
        'age': np.random.randn(n)
    }
    df = pd.DataFrame(data)

    # Run diagnostics
    results = run_collinearity_diagnostics(df, vif_threshold=5.0)

    assert 'valid_predictors' in results
    assert 'vif_values' in results
    assert 'status' in results

    # Check that VIF values are positive
    for p, v in results['vif_values'].items():
        assert v > 0


def test_save_collinearity_report():
    """Test writing of VIF diagnostics to log and JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = os.path.join(tmpdir, "vif_diagnostics.log")
        json_path = os.path.join(tmpdir, "vif_valid_predictors.json")

        results = {
            'valid_predictors': ['Fatigue_Delta', 'Pre_Complexity'],
            'vif_values': {'Fatigue_Delta': 1.2, 'Pre_Complexity': 1.5},
            'status': 'completed'
        }

        save_collinearity_report(results, log_path, json_path)

        # Check JSON file exists and has correct content
        assert os.path.exists(json_path)
        with open(json_path, 'r') as f:
            data = json.load(f)
        assert 'valid_predictors' in data
        assert set(data['valid_predictors']) == set(['Fatigue_Delta', 'Pre_Complexity'])

        # Check log file exists
        assert os.path.exists(log_path)