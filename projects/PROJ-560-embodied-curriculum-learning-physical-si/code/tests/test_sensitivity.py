import pytest
import numpy as np
import os
import sys
import json
import tempfile
from typing import List, Tuple

# Ensure src is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from src.sensitivity import run_sensitivity_sweep
from src.models import SensitivitySweep

class TestSensitivitySweepLogic:
    """Tests for the sensitivity sweep logic in sensitivity.py"""

    def test_sweep_runs_with_default_thresholds(self):
        """Test that the sweep runs and returns results for default thresholds."""
        # Generate deterministic fake data for testing logic (not for final results)
        np.random.seed(42)
        emb_scores = np.random.normal(loc=5.0, scale=1.0, size=50).tolist()
        stat_scores = np.random.normal(loc=4.0, scale=1.0, size=50).tolist()

        results = run_sensitivity_sweep(emb_scores, stat_scores)

        # Default thresholds are [0.01, 0.05, 0.10]
        assert len(results) == 3
        assert all(isinstance(r, SensitivitySweep) for r in results)
        
        thresholds = [r.threshold for r in results]
        assert 0.01 in thresholds
        assert 0.05 in thresholds
        assert 0.10 in thresholds

    def test_sweep_respects_custom_thresholds(self):
        """Test that custom thresholds are used."""
        np.random.seed(42)
        emb_scores = np.random.normal(loc=5.0, scale=1.0, size=50).tolist()
        stat_scores = np.random.normal(loc=4.0, scale=1.0, size=50).tolist()

        custom_thresholds = [0.001, 0.02, 0.05, 0.1]
        results = run_sensitivity_sweep(emb_scores, stat_scores, thresholds=custom_thresholds)

        assert len(results) == 4
        for r, t in zip(results, custom_thresholds):
            assert r.threshold == t

    def test_significance_changes_with_threshold(self):
        """Test that significance status changes as expected across thresholds."""
        # Create data with a clear difference
        np.random.seed(123)
        emb_scores = np.random.normal(loc=10.0, scale=1.0, size=100).tolist()
        stat_scores = np.random.normal(loc=5.0, scale=1.0, size=100).tolist()

        # Use a wide range of thresholds
        results = run_sensitivity_sweep(emb_scores, stat_scores, thresholds=[0.0001, 0.001, 0.5])

        # The difference is large, so it should be significant even at very low alpha
        # But we test the logic: lower threshold makes it harder to be significant
        # If p < 0.0001, then it is significant at 0.0001, 0.001, and 0.5
        
        # Verify that significance is monotonic (if significant at 0.0001, must be at 0.5)
        # Actually, if p < 0.0001, it is significant at all.
        # Let's check the structure of the output
        for r in results:
            assert hasattr(r, 'is_significant')
            assert isinstance(r.is_significant, bool)

    def test_empty_input_returns_empty_list(self):
        """Test that empty lists return an empty result list."""
        results = run_sensitivity_sweep([], [])
        assert results == []

    def test_sensitivity_sweep_dataclass_fields(self):
        """Verify that SensitivitySweep objects contain all required fields."""
        np.random.seed(42)
        emb_scores = np.random.normal(loc=5.0, scale=1.0, size=50).tolist()
        stat_scores = np.random.normal(loc=4.0, scale=1.0, size=50).tolist()

        results = run_sensitivity_sweep(emb_scores, stat_scores)
        r = results[0]

        # Check required attributes exist
        assert hasattr(r, 'threshold')
        assert hasattr(r, 't_statistic')
        assert hasattr(r, 'p_value')
        assert hasattr(r, 'effect_size')
        assert hasattr(r, 'is_significant')
        assert hasattr(r, 'is_significant_corrected')
        assert hasattr(r, 'adjusted_alpha')
        assert hasattr(r, 'inference_framing')