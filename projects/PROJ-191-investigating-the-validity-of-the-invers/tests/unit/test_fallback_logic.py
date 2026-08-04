"""
Unit tests for fallback logic in code/data/fallback_logic.py
"""
import pytest
import numpy as np
import pandas as pd
from dataclasses import dataclass
from pathlib import Path
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from data.loaders import HarmonizedDataset
from data.fallback_logic import detect_independent_runs, bootstrap_resample_dataset, prepare_analysis_dataset

@pytest.fixture
def single_run_dataset():
    """Create a dataset with a single run."""
    sep = np.array([1e-5, 2e-5, 3e-5])
    force = np.array([-1e-15, -2e-15, -3e-15])
    cov = np.eye(3) * 1e-30
    meta = [{'run_id': 'run_1'}]
    return HarmonizedDataset(separation=sep, force=force, covariance_matrix=cov, run_metadata=meta)

@pytest.fixture
def three_run_dataset():
    """Create a dataset with three runs."""
    sep = np.array([1e-5, 2e-5, 3e-5, 4e-5, 5e-5, 6e-5])
    force = np.array([-1e-15, -2e-15, -3e-15, -4e-15, -5e-15, -6e-15])
    cov = np.eye(6) * 1e-30
    meta = [{'run_id': 'run_1'}, {'run_id': 'run_2'}, {'run_id': 'run_3'}]
    return HarmonizedDataset(separation=sep, force=force, covariance_matrix=cov, run_metadata=meta)

@pytest.fixture
def two_run_dataset():
    """Create a dataset with two runs."""
    sep = np.array([1e-5, 2e-5, 3e-5, 4e-5])
    force = np.array([-1e-15, -2e-15, -3e-15, -4e-15])
    cov = np.eye(4) * 1e-30
    meta = [{'run_id': 'run_1'}, {'run_id': 'run_2'}]
    return HarmonizedDataset(separation=sep, force=force, covariance_matrix=cov, run_metadata=meta)

def test_detect_independent_runs_single(single_run_dataset):
    n = detect_independent_runs(single_run_dataset)
    assert n == 1

def test_detect_independent_runs_three(three_run_dataset):
    n = detect_independent_runs(three_run_dataset)
    assert n == 3

def test_detect_independent_runs_two(two_run_dataset):
    n = detect_independent_runs(two_run_dataset)
    assert n == 2

def test_bootstrap_resample_dataset_single(single_run_dataset):
    samples = bootstrap_resample_dataset(single_run_dataset, n_bootstrap=5, random_state=42)
    assert len(samples) == 5
    for s in samples:
        assert len(s.separation) == len(single_run_dataset.separation)
        assert len(s.force) == len(single_run_dataset.force)

def test_prepare_analysis_dataset_fallback(two_run_dataset):
    # Should trigger bootstrap flag
    ds, is_bootstrap = prepare_analysis_dataset(two_run_dataset, min_runs_required=3)
    assert is_bootstrap is True
    assert ds is two_run_dataset

def test_prepare_analysis_dataset_normal(three_run_dataset):
    # Should NOT trigger bootstrap flag
    ds, is_bootstrap = prepare_analysis_dataset(three_run_dataset, min_runs_required=3)
    assert is_bootstrap is False
    assert ds is three_run_dataset
