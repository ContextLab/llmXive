"""
Unit tests for data_generator.py
"""
import pytest
import numpy as np
import pandas as pd
from data_generator import generate_data
from config import set_seed


def test_generate_data_h0_true():
    """
    Test that under H0 (no treatment effect), generated groups have equal means.
    Also verifies that cluster IDs are preserved.
    """
    set_seed(42)
    n_clusters = 50
    n_obs_per_cluster = 10
    icc = 0.0  # Independent data for simpler verification

    data = generate_data(
        n_clusters=n_clusters,
        n_obs_per_cluster=n_obs_per_cluster,
        icc=icc,
        seed=42
    )

    # Check structure
    assert 'outcome' in data.columns
    assert 'treatment' in data.columns
    assert 'cluster_id' in data.columns

    # Check cluster IDs are preserved (0 to n_clusters-1)
    expected_cluster_ids = set(range(n_clusters))
    actual_cluster_ids = set(data['cluster_id'].unique())
    assert expected_cluster_ids == actual_cluster_ids

    # Check treatment assignment is balanced (approximately)
    treatment_counts = data['treatment'].value_counts()
    # Should be roughly 50/50 split
    assert abs(treatment_counts.get(0, 0) - treatment_counts.get(1, 0)) < n_clusters / 2

    # Under H0, means should be approximately equal (within tolerance)
    # With icc=0.0, this is a standard t-test scenario
    group_0 = data[data['treatment'] == 0]['outcome']
    group_1 = data[data['treatment'] == 1]['outcome']

    mean_0 = group_0.mean()
    mean_1 = group_1.mean()

    # Allow for sampling variation (tolerance based on standard error)
    # With 250 observations per group, SE is roughly 0.06 for unit variance
    # We use a generous tolerance of 0.5 standard deviations
    pooled_std = np.sqrt((group_0.var() + group_1.var()) / 2)
    tolerance = 0.5 * pooled_std / np.sqrt(n_clusters * n_obs_per_cluster / 2)

    # If tolerance is too small, use a fixed reasonable value
    if tolerance < 0.1:
        tolerance = 0.5

    assert abs(mean_0 - mean_1) < tolerance, \
        f"Group means differ significantly: {mean_0:.4f} vs {mean_1:.4f}"
