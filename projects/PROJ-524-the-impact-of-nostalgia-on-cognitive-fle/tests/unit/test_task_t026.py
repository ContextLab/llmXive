"""
Unit tests for code/task_t026_sensitivity_sweep.py.
Tests sensitivity sweep across multiple thresholds.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.task_t026_sensitivity_sweep import (
    run_sensitivity_sweep
)


class TestRunSensitivitySweep:
    def test_run_sensitivity_sweep_basic(self):
        """Test basic sensitivity sweep."""
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia'] * 30 + ['control'] * 30,
            'perseverative_errors': np.concatenate([
                np.random.normal(25, 5, 30),
                np.random.normal(30, 5, 30)
            ])
        })

        thresholds = [0.01, 0.05, 0.10]
        results = run_sensitivity_sweep(df, thresholds, 'perseverative_errors')

        assert len(results) == len(thresholds)
        for i, r in enumerate(results):
            assert r['threshold'] == thresholds[i]
            assert 'is_significant' in r
            assert 'p_value' in r

    def test_run_sensitivity_sweep_all_significant(self):
        """Test sweep where all thresholds yield significant results."""
        np.random.seed(42)
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia'] * 50 + ['control'] * 50,
            'perseverative_errors': np.concatenate([
                np.random.normal(20, 3, 50),
                np.random.normal(30, 3, 50)
            ])
        })

        thresholds = [0.001, 0.01, 0.05, 0.10]
        results = run_sensitivity_sweep(df, thresholds, 'perseverative_errors')

        assert all(r['is_significant'] for r in results)

    def test_run_sensitivity_sweep_none_significant(self):
        """Test sweep where no thresholds yield significant results."""
        np.random.seed(42)
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia'] * 30 + ['control'] * 30,
            'perseverative_errors': np.concatenate([
                np.random.normal(25, 5, 30),
                np.random.normal(26, 5, 30)  # Very small difference
            ])
        })

        thresholds = [0.01, 0.05, 0.10]
        results = run_sensitivity_sweep(df, thresholds, 'perseverative_errors')

        assert not any(r['is_significant'] for r in results)

    def test_run_sensitivity_sweep_borderline(self):
        """Test sweep with borderline p-values."""
        np.random.seed(42)
        # Create data with p-value near 0.05
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia'] * 40 + ['control'] * 40,
            'perseverative_errors': np.concatenate([
                np.random.normal(25, 5, 40),
                np.random.normal(28, 5, 40)
            ])
        })

        thresholds = [0.04, 0.05, 0.06]
        results = run_sensitivity_sweep(df, thresholds, 'perseverative_errors')

        # Should show sensitivity to threshold
        significant_count = sum(1 for r in results if r['is_significant'])
        assert significant_count > 0 and significant_count < len(thresholds)