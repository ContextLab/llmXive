import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from stats_engine import sensitivity_analysis

def test_sensitivity_analysis_empty_dataframe():
    """Test that sensitivity analysis handles empty DataFrames gracefully."""
    df = pd.DataFrame(columns=['metric_a', 'metric_b', 'p_value', 'adj_p_value'])
    result = sensitivity_analysis(df)
    assert result.empty
    assert list(result.columns) == ['threshold', 'count_significant', 'significant_pairs']

def test_sensitivity_analysis_no_significant():
    """Test sensitivity analysis when no correlations are significant."""
    data = {
        'metric_a': ['A', 'B'],
        'metric_b': ['C', 'D'],
        'p_value': [0.5, 0.6],
        'adj_p_value': [0.7, 0.8]
    }
    df = pd.DataFrame(data)
    result = sensitivity_analysis(df)

    assert not result.empty
    assert result['count_significant'].sum() == 0
    assert set(result['threshold'].unique()) == {0.01, 0.05, 0.10, 0.20}

def test_sensitivity_analysis_some_significant():
    """Test sensitivity analysis with some significant correlations."""
    data = {
        'metric_a': ['A', 'B', 'C'],
        'metric_b': ['D', 'E', 'F'],
        'p_value': [0.03, 0.07, 0.15],
        'adj_p_value': [0.04, 0.08, 0.16]
    }
    df = pd.DataFrame(data)
    result = sensitivity_analysis(df)

    assert not result.empty
    # At threshold 0.05, only first should be significant (0.04 < 0.05)
    row_005 = result[result['threshold'] == 0.05]
    assert len(row_005) == 1
    assert row_005['count_significant'].iloc[0] == 1

    # At threshold 0.10, first two should be significant
    row_010 = result[result['threshold'] == 0.10]
    assert len(row_010) == 1
    assert row_010['count_significant'].iloc[0] == 2

    # At threshold 0.20, all three should be significant
    row_020 = result[result['threshold'] == 0.20]
    assert len(row_020) == 1
    assert row_020['count_significant'].iloc[0] == 3

def test_sensitivity_analysis_thresholds():
    """Test that all expected thresholds are present."""
    data = {
        'metric_a': ['A'],
        'metric_b': ['B'],
        'p_value': [0.001],
        'adj_p_value': [0.002]
    }
    df = pd.DataFrame(data)
    result = sensitivity_analysis(df)

    expected_thresholds = {0.01, 0.05, 0.10, 0.20}
    assert set(result['threshold'].unique()) == expected_thresholds
    assert all(result['count_significant'] == 1)  # All should be significant