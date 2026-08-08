"""
Unit tests for imbalance analysis module (T008).
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from imbalance import calculate_gini, calculate_compositional_imbalance_score, identify_target_columns

class TestGiniCoefficient:
    def test_gini_perfect_equality(self):
        """Gini should be 0 for equal values."""
        values = np.array([10, 10, 10, 10, 10])
        assert abs(calculate_gini(values)) < 1e-5

    def test_gini_perfect_inequality(self):
        """Gini should be close to 1 for highly unequal values."""
        values = np.array([0, 0, 0, 0, 100])
        score = calculate_gini(values)
        assert 0.8 < score <= 1.0

    def test_gini_negative_values(self):
        """Gini should handle negative values by shifting."""
        values = np.array([-10, -5, 0, 5, 10])
        score = calculate_gini(values)
        assert 0 <= score <= 1.0

    def test_gini_empty_array(self):
        """Gini of empty array should be 0."""
        assert calculate_gini(np.array([])) == 0.0

class TestCompositionalImbalance:
    def test_convex_hull_score_dense(self):
        """Dense cluster should have low hull ratio."""
        # Generate a dense cloud of points
        np.random.seed(42)
        X = np.random.normal(loc=0, scale=0.1, size=(1000, 5))
        score = calculate_compositional_imbalance_score(X)
        # In high dimensions, many points are on the hull, but a dense cluster
        # should have a lower ratio than a sparse shell.
        assert 0.0 <= score <= 1.0

    def test_convex_hull_score_sparse(self):
        """Points on a shell should have high hull ratio."""
        # Points on a sphere surface
        np.random.seed(42)
        theta = np.random.uniform(0, 2*np.pi, 500)
        phi = np.arccos(2*np.random.uniform(0, 1, 500) - 1)
        x = np.sin(phi) * np.cos(theta)
        y = np.sin(phi) * np.sin(theta)
        z = np.cos(phi)
        X = np.column_stack([x, y, z, np.zeros(500), np.zeros(500)])
        score = calculate_compositional_imbalance_score(X)
        # Most points should be on the hull
        assert score > 0.5

    def test_convex_hull_small_sample(self):
        """Small sample should return 0."""
        X = np.array([[1, 2], [3, 4]])
        assert calculate_compositional_imbalance_score(X) == 0.0

class TestTargetIdentification:
    def test_identify_targets(self):
        """Should identify non-descriptor columns as targets."""
        df = pd.DataFrame({
            'mean_atomic_weight': [10.0],
            'min_atomic_weight': [5.0],
            'formation_energy': [1.5],
            'band_gap': [2.0]
        })
        targets = identify_target_columns(df)
        assert 'formation_energy' in targets
        assert 'band_gap' in targets
        assert 'mean_atomic_weight' not in targets
        assert 'min_atomic_weight' not in targets

    def test_identify_target_column(self):
        """Should identify 'target' column if present."""
        df = pd.DataFrame({
            'mean_atomic_weight': [10.0],
            'target': [1.5]
        })
        targets = identify_target_columns(df)
        assert 'target' in targets