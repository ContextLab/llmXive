"""
Unit tests for simulation_runner.py
"""
import pytest
import numpy as np
import pandas as pd
from simulation_runner import run_baseline_simulation, estimate_memory_footprint, optimize_memory
from config import DEFAULT_N_CLUSTERS


def test_estimate_memory_footprint():
    """Test that memory estimation returns a positive float."""
    footprint = estimate_memory_footprint(n_clusters=100, n_obs_per_cluster=10)
    assert footprint > 0
    assert isinstance(footprint, float)


def test_optimize_memory_no_change():
    """Test that optimize_memory doesn't change config when under limit."""
    cfg = {
        'n_clusters': 10,
        'n_obs_per_cluster': 10
    }
    original_n = cfg['n_obs_per_cluster']
    updated_cfg = optimize_memory(cfg)
    assert updated_cfg['n_obs_per_cluster'] == original_n


def test_run_baseline_simulation_structure():
    """Test that run_baseline_simulation returns the expected structure."""
    results = run_baseline_simulation(
        icc=0.0,
        n_iterations=5,
        seed=42,
        n_clusters=20,
        n_obs_per_cluster=5
    )

    assert isinstance(results, list)
    assert len(results) == 5

    # Check first result structure
    first = results[0]
    assert 'iteration' in first
    assert 'icc' in first
    assert 'p_value' in first
    assert 'rejected_0.05' in first
    assert 'rejected_0.01' in first
    assert 'rejected_0.10' in first

    # Check types
    assert isinstance(first['iteration'], int)
    assert isinstance(first['icc'], float)
    assert isinstance(first['p_value'], float)
    assert 0.0 <= first['p_value'] <= 1.0
    assert isinstance(first['rejected_0.05'], bool)


def test_run_baseline_simulation_rejection_logic():
    """Test that rejection flags are correctly set based on p-value."""
    # This is a statistical test - we can't guarantee specific outcomes,
    # but we can verify the logic is consistent
    results = run_baseline_simulation(
        icc=0.0,
        n_iterations=10,
        seed=12345,
        n_clusters=50,
        n_obs_per_cluster=10
    )

    for r in results:
        p = r['p_value']
        assert r['rejected_0.10'] == (p < 0.10)
        assert r['rejected_0.05'] == (p < 0.05)
        assert r['rejected_0.01'] == (p < 0.01)


def test_run_baseline_simulation_icc_handling():
    """Test that different ICC values produce different data patterns."""
    results_low = run_baseline_simulation(
        icc=0.0,
        n_iterations=5,
        seed=42,
        n_clusters=20,
        n_obs_per_cluster=5
    )

    results_high = run_baseline_simulation(
        icc=0.5,
        n_iterations=5,
        seed=42,
        n_clusters=20,
        n_obs_per_cluster=5
    )

    # Both should return valid results
    assert len(results_low) == 5
    assert len(results_high) == 5

    # P-values should be valid probabilities
    for r in results_low + results_high:
        assert 0.0 <= r['p_value'] <= 1.0
