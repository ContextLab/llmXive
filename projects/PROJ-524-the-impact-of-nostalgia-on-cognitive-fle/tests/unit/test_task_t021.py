"""
Unit tests for code/task_t021_power_analysis.py.
Tests power analysis calculations.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.task_t021_power_analysis import (
    calculate_power_and_mdes
)


class TestCalculatePowerAndMDES:
    def test_calculate_power_and_mdes_basic(self):
        """Test basic power and MDES calculation."""
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia'] * 30 + ['control'] * 30,
            'perseverative_errors': np.concatenate([
                np.random.normal(25, 5, 30),
                np.random.normal(30, 5, 30)
            ])
        })

        results = calculate_power_and_mdes(df, 'perseverative_errors', alpha=0.05)

        assert 'power' in results
        assert 'mdes' in results
        assert 0 <= results['power'] <= 1
        assert results['mdes'] > 0

    def test_calculate_power_and_mdes_large_sample(self):
        """Test power with large sample size."""
        np.random.seed(42)
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia'] * 100 + ['control'] * 100,
            'perseverative_errors': np.concatenate([
                np.random.normal(25, 5, 100),
                np.random.normal(30, 5, 100)
            ])
        })

        results = calculate_power_and_mdes(df, 'perseverative_errors', alpha=0.05)

        # Large sample should yield high power
        assert results['power'] > 0.8

    def test_calculate_power_and_mdes_small_sample(self):
        """Test power with small sample size."""
        np.random.seed(42)
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia'] * 10 + ['control'] * 10,
            'perseverative_errors': np.concatenate([
                np.random.normal(25, 5, 10),
                np.random.normal(30, 5, 10)
            ])
        })

        results = calculate_power_and_mdes(df, 'perseverative_errors', alpha=0.05)

        # Small sample may have lower power
        assert 0 <= results['power'] <= 1

    def test_calculate_power_and_mdes_no_effect(self):
        """Test power when there is no effect."""
        np.random.seed(42)
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia'] * 30 + ['control'] * 30,
            'perseverative_errors': np.concatenate([
                np.random.normal(25, 5, 30),
                np.random.normal(25, 5, 30)  # Same mean
            ])
        })

        results = calculate_power_and_mdes(df, 'perseverative_errors', alpha=0.05)

        # Power should be low when effect is zero
        assert results['power'] < 0.5
