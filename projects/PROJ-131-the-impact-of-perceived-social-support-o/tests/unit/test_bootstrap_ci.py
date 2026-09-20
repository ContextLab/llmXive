"""
Unit tests for bootstrapping logic (T019).
Verifies that bootstrap CI calculation works correctly.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from analysis.bootstrap_ci import compute_bca_bootstrap_ci, load_seed_config

def test_load_seed_config():
    """Test loading seed config."""
    seed = load_seed_config()
    assert isinstance(seed, int)

def test_compute_bca_bootstrap_ci():
    """Test BCa bootstrap CI computation."""
    # Create a simple dataset
    data = np.random.normal(loc=50, scale=10, size=1000)
    stat_func = lambda x: np.mean(x)

    # Run bootstrap
    ci = compute_bca_bootstrap_ci(data, stat_func, n_resamples=100, seed=42)

    assert isinstance(ci, tuple)
    assert len(ci) == 2
    assert ci[0] < ci[1]