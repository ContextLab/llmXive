"""
Unit tests for proxy validation logic (T014).
"""
import os
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Import the functions to test
# We need to adjust the import path if running from tests/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from proxy_validation import (
    calculate_proxy_utility,
    validate_proxy_correlation,
    MIN_HOLDOUT_SIZE,
    CORRELATION_THRESHOLD
)


def test_calculate_proxy_utility():
    """Test proxy utility calculation from static logs."""
    data = [
        {'trajectory_id': 't1', 'layers_used': ['layer_a', 'layer_b']},
        {'trajectory_id': 't1', 'layers_used': ['layer_a']},
        {'trajectory_id': 't2', 'layers_used': ['layer_b', 'layer_c']}
    ]

    records = []
    for r in data:
        for layer in r['layers_used']:
            records.append({'trajectory_id': r['trajectory_id'], 'layer_name': layer, 'used': 1})

    df = pd.DataFrame(records)
    result = calculate_proxy_utility(df)

    assert not result.empty
    assert 'proxy_utility' in result.columns
    assert 'trajectory_id' in result.columns
    assert 'layer_name' in result.columns

    # Check specific values
    # t1, layer_a: used 2 times
    row_ta = result[(result['trajectory_id'] == 't1') & (result['layer_name'] == 'layer_a')]
    assert len(row_ta) == 1
    assert row_ta['proxy_utility'].iloc[0] == 2


def test_validate_proxy_correlation_high():
    """Test validation when correlation is high."""
    # Create mock data with perfect correlation
    n = MIN_HOLDOUT_SIZE + 10
    proxy_vals = list(range(n))
    ablation_vals = [x * 2 for x in proxy_vals]  # Perfect linear relationship

    proxy_df = pd.DataFrame({
        'trajectory_id': [f't{i}' for i in range(n)],
        'layer_name': ['layer_a'] * n,
        'proxy_utility': proxy_vals
    })

    ablation_df = pd.DataFrame({
        'trajectory_id': [f't{i}' for i in range(n)],
        'layer_name': ['layer_a'] * n,
        'ablation_utility': ablation_vals
    })

    report = validate_proxy_correlation(proxy_df, ablation_df)

    assert report['proxy_valid'] is True
    assert report['correlation'] is not None
    assert report['correlation'] >= CORRELATION_THRESHOLD
    assert report['sample_size'] == n


def test_validate_proxy_correlation_low():
    """Test validation when correlation is low."""
    n = MIN_HOLDOUT_SIZE + 10
    # Create uncorrelated data
    proxy_vals = list(range(n))
    ablation_vals = np.random.permutation(proxy_vals).tolist()  # Shuffle to break correlation

    proxy_df = pd.DataFrame({
        'trajectory_id': [f't{i}' for i in range(n)],
        'layer_name': ['layer_a'] * n,
        'proxy_utility': proxy_vals
    })

    ablation_df = pd.DataFrame({
        'trajectory_id': [f't{i}' for i in range(n)],
        'layer_name': ['layer_a'] * n,
        'ablation_utility': ablation_vals
    })

    report = validate_proxy_correlation(proxy_df, ablation_df)

    assert report['proxy_valid'] is False
    assert report['correlation'] is not None
    assert report['correlation'] < CORRELATION_THRESHOLD


def test_validate_proxy_correlation_small_sample():
    """Test validation when sample size is too small."""
    n = 5  # Less than MIN_HOLDOUT_SIZE
    proxy_vals = list(range(n))
    ablation_vals = list(range(n))

    proxy_df = pd.DataFrame({
        'trajectory_id': [f't{i}' for i in range(n)],
        'layer_name': ['layer_a'] * n,
        'proxy_utility': proxy_vals
    })

    ablation_df = pd.DataFrame({
        'trajectory_id': [f't{i}' for i in range(n)],
        'layer_name': ['layer_a'] * n,
        'ablation_utility': ablation_vals
    })

    report = validate_proxy_correlation(proxy_df, ablation_df)

    assert report['proxy_valid'] is False
    assert 'Sample size' in report['reason']
    assert report['sample_size'] == n


def test_validate_proxy_correlation_empty():
    """Test validation when data is empty."""
    proxy_df = pd.DataFrame(columns=['trajectory_id', 'layer_name', 'proxy_utility'])
    ablation_df = pd.DataFrame(columns=['trajectory_id', 'layer_name', 'ablation_utility'])

    report = validate_proxy_correlation(proxy_df, ablation_df)

    assert report['proxy_valid'] is False
    assert report['reason'] == 'Input data empty'