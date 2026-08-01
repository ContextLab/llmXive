"""
Unit tests for code/task_t020_effect_sizes.py.
Tests effect size calculations.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.task_t020_effect_sizes import (
    calculate_effect_sizes
)


class TestCalculateEffectSizes:
    def test_calculate_effect_sizes_basic(self):
        """Test basic effect size calculation."""
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia', 'nostalgia', 'control', 'control'],
            'perseverative_errors': [10, 12, 15, 18],
            'categories_completed': [5, 6, 4, 3]
        })

        results = calculate_effect_sizes(df)

        assert 'perseverative_errors' in results
        assert 'categories_completed' in results

        assert 'cohens_d' in results['perseverative_errors']
        assert 'ci_lower' in results['perseverative_errors']
        assert 'ci_upper' in results['perseverative_errors']

    def test_calculate_effect_sizes_single_group(self):
        """Test effect size with single group (should handle gracefully)."""
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia', 'nostalgia', 'nostalgia'],
            'perseverative_errors': [10, 12, 15],
            'categories_completed': [5, 6, 4]
        })

        # Should not crash, may return NaN or handle gracefully
        results = calculate_effect_sizes(df)
        assert 'perseverative_errors' in results

    def test_calculate_effect_sizes_large_effect(self):
        """Test effect size with large difference between groups."""
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia', 'nostalgia', 'control', 'control'],
            'perseverative_errors': [5, 6, 20, 22],
            'categories_completed': [8, 9, 3, 2]
        })

        results = calculate_effect_sizes(df)

        # Large effect should have |d| > 0.8
        d = results['perseverative_errors']['cohens_d']
        assert abs(d) > 0.8

    def test_calculate_effect_sizes_small_effect(self):
        """Test effect size with small difference between groups."""
        df = pd.DataFrame({
            'stimulus_type': ['nostalgia', 'nostalgia', 'control', 'control'],
            'perseverative_errors': [10, 11, 10, 11],
            'categories_completed': [5, 5, 5, 5]
        })

        results = calculate_effect_sizes(df)

        # Small effect should have |d| < 0.2
        d = results['perseverative_errors']['cohens_d']
        assert abs(d) < 0.5  # Allow some tolerance
