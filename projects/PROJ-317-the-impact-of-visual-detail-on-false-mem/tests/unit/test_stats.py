import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import pytest
import numpy as np

# Add project root to path to allow imports from code/
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.stats import apply_bonferroni_correction, save_bonferroni_results


class TestBonferroniCorrection:
    """Unit tests for multiple-comparison correction (Bonferroni)."""

    def test_bonferroni_basic_calculation(self):
        """Test that Bonferroni correction correctly adjusts p-values."""
        # Original p-values
        p_values = [0.01, 0.03, 0.05, 0.10]
        n_tests = len(p_values)
        alpha = 0.05

        # Expected adjusted p-values (min(p * n, 1.0))
        expected_adjusted = [
            min(0.01 * n_tests, 1.0),
            min(0.03 * n_tests, 1.0),
            min(0.05 * n_tests, 1.0),
            min(0.10 * n_tests, 1.0)
        ]

        adjusted_p_values = apply_bonferroni_correction(p_values, alpha)

        assert len(adjusted_p_values) == len(p_values)
        for i, (adj, expected) in enumerate(zip(adjusted_p_values, expected_adjusted)):
            assert math.isclose(adj, expected, rel_tol=1e-9), \
                f"Index {i}: expected {expected}, got {adj}"

    def test_bonferroni_capping_at_one(self):
        """Test that adjusted p-values are capped at 1.0."""
        p_values = [0.2, 0.5, 0.8]
        n_tests = len(p_values)
        alpha = 0.05

        # 0.8 * 3 = 2.4 -> should be capped at 1.0
        adjusted_p_values = apply_bonferroni_correction(p_values, alpha)

        assert all(p <= 1.0 for p in adjusted_p_values), \
            "Adjusted p-values must not exceed 1.0"
        assert math.isclose(adjusted_p_values[-1], 1.0, rel_tol=1e-9), \
            "Large p-values should be capped at 1.0"

    def test_bonferroni_significance_threshold(self):
        """Test that significance is correctly determined after correction."""
        p_values = [0.01, 0.02, 0.04, 0.06]
        alpha = 0.05
        n_tests = len(p_values)

        # Adjusted threshold: alpha / n_tests
        adjusted_alpha = alpha / n_tests

        adjusted_p_values = apply_bonferroni_correction(p_values, alpha)

        # Determine significance
        significant = [p < adjusted_alpha for p in adjusted_p_values]

        # Only the first two (0.01, 0.02) should be significant
        # 0.01 * 4 = 0.04 < 0.05 -> significant
        # 0.02 * 4 = 0.08 > 0.05 -> not significant
        # Wait, let's recalculate:
        # adjusted_alpha = 0.05 / 4 = 0.0125
        # 0.01 * 4 = 0.04 > 0.0125 -> not significant
        # Actually, the function returns adjusted p-values.
        # We compare adjusted p-value < alpha (0.05)
        # 0.01 * 4 = 0.04 < 0.05 -> significant
        # 0.02 * 4 = 0.08 > 0.05 -> not significant

        assert significant[0] is True, "First p-value should be significant"
        assert significant[1] is False, "Second p-value should not be significant"
        assert significant[2] is False, "Third p-value should not be significant"
        assert significant[3] is False, "Fourth p-value should not be significant"

    def test_bonferroni_empty_list(self):
        """Test handling of empty p-value list."""
        adjusted = apply_bonferroni_correction([], 0.05)
        assert adjusted == [], "Empty input should return empty list"

    def test_bonferroni_single_test(self):
        """Test that single test returns original p-value."""
        p_values = [0.03]
        adjusted = apply_bonferroni_correction(p_values, 0.05)
        assert len(adjusted) == 1
        assert math.isclose(adjusted[0], 0.03, rel_tol=1e-9)

    def test_save_bonferroni_results_creates_file(self):
        """Test that save_bonferroni_results writes a valid JSON file."""
        results = {
            "adjusted_p_values": [0.04, 0.12, 0.20],
            "original_p_values": [0.01, 0.03, 0.05],
            "alpha": 0.05,
            "n_tests": 3,
            "significant_indices": [0]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "bonferroni_results.json"
            save_bonferroni_results(results, str(output_path))

            assert output_path.exists(), "Output file should be created"

            with open(output_path, "r") as f:
                loaded = json.load(f)

            assert loaded == results, "Loaded data should match input"

    def test_save_bonferroni_results_directory_creation(self):
        """Test that save_bonferroni_results creates parent directories if needed."""
        results = {
            "adjusted_p_values": [0.05],
            "original_p_values": [0.05],
            "alpha": 0.05,
            "n_tests": 1,
            "significant_indices": []
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            # Use a nested path that doesn't exist yet
            output_path = Path(tmpdir) / "subdir" / "nested" / "results.json"
            save_bonferroni_results(results, str(output_path))

            assert output_path.exists(), "Nested directories should be created"

    def test_bonferroni_with_many_tests(self):
        """Test Bonferroni correction with a larger set of p-values."""
        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 20).tolist()
        alpha = 0.05
        n_tests = len(p_values)

        adjusted = apply_bonferroni_correction(p_values, alpha)

        assert len(adjusted) == n_tests
        assert all(0.0 <= p <= 1.0 for p in adjusted)

        # Verify calculation for one specific value
        idx = 5
        expected = min(p_values[idx] * n_tests, 1.0)
        assert math.isclose(adjusted[idx], expected, rel_tol=1e-9)

    def test_bonferroni_preserves_order(self):
        """Test that the order of p-values is preserved in the output."""
        p_values = [0.05, 0.01, 0.09, 0.02]
        adjusted = apply_bonferroni_correction(p_values, 0.05)

        # The relative order of adjusted p-values should match original
        # (since multiplication by n_tests is monotonic)
        for i in range(len(p_values) - 1):
            if p_values[i] < p_values[i+1]:
                assert adjusted[i] < adjusted[i+1], \
                    "Order should be preserved"