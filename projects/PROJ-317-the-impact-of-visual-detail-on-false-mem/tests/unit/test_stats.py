"""
Unit tests for statistical analysis functions in code/analysis/stats.py.

Tests cover:
- Power analysis calculations
- Repeated-measures ANOVA execution
- Multiple-comparison correction (Bonferroni)
- Dataset fit checking
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
from scipy import stats as scipy_stats

# Import the functions under test using the project's API surface
import sys
# Ensure the code directory is in the path for imports
project_root = Path(__file__).parent.parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from analysis.stats import (
    calculate_anova_power,
    save_power_analysis,
    run_repeated_measures_anova,
    apply_bonferroni_correction,
    save_bonferroni_results,
    check_dataset_fit
)
from config import get_processed_dir


class TestBonferroniCorrection:
    """Tests for the multiple-comparison correction logic (T033)."""

    def test_bonferroni_single_pvalue(self):
        """Test correction on a single p-value."""
        p_values = [0.05]
        alpha = 0.05
        corrected = apply_bonferroni_correction(p_values, alpha)
        
        # With one test, adjusted p-value should be the same (or capped at 1.0)
        # Bonferroni: p_adj = p * n. Here n=1, so p_adj = 0.05
        assert len(corrected) == 1
        assert abs(corrected[0]["adjusted_p"] - 0.05) < 1e-9
        assert corrected[0]["significant"] is False  # 0.05 is typically not < 0.05

    def test_bonferroni_multiple_pvalues_significant(self):
        """Test correction where some remain significant."""
        # Simulate p-values: one very small, one medium, one large
        p_values = [0.001, 0.02, 0.10]
        alpha = 0.05
        n_tests = len(p_values)
        
        corrected = apply_bonferroni_correction(p_values, alpha)
        
        assert len(corrected) == 3
        
        # Check calculation: p_adj = p * n
        expected_0 = 0.001 * n_tests
        expected_1 = 0.02 * n_tests
        expected_2 = 0.10 * n_tests
        
        assert abs(corrected[0]["adjusted_p"] - expected_0) < 1e-9
        assert abs(corrected[1]["adjusted_p"] - expected_1) < 1e-9
        assert abs(corrected[2]["adjusted_p"] - expected_2) < 1e-9
        
        # Check significance (p_adj < alpha)
        # 0.003 < 0.05 -> True
        # 0.06 < 0.05 -> False
        # 0.30 < 0.05 -> False
        assert corrected[0]["significant"] is True
        assert corrected[1]["significant"] is False
        assert corrected[2]["significant"] is False

    def test_bonferroni_capped_at_one(self):
        """Test that adjusted p-values are capped at 1.0."""
        p_values = [0.8, 0.9]
        alpha = 0.05
        n_tests = 2
        
        corrected = apply_bonferroni_correction(p_values, alpha)
        
        # 0.8 * 2 = 1.6 -> should be capped to 1.0
        # 0.9 * 2 = 1.8 -> should be capped to 1.0
        assert corrected[0]["adjusted_p"] == 1.0
        assert corrected[1]["adjusted_p"] == 1.0
        assert corrected[0]["significant"] is False
        assert corrected[1]["significant"] is False

    def test_bonferroni_empty_list(self):
        """Test handling of empty p-value list."""
        p_values = []
        alpha = 0.05
        
        corrected = apply_bonferroni_correction(p_values, alpha)
        
        assert corrected == []

    def test_bonferroni_save_results(self):
        """Test that save_bonferroni_results writes valid JSON."""
        p_values = [0.01, 0.04, 0.06]
        alpha = 0.05
        corrected_data = apply_bonferroni_correction(p_values, alpha)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "bonferroni_results.json"
            save_bonferroni_results(corrected_data, str(output_path))
            
            assert output_path.exists()
            
            with open(output_path, "r") as f:
                loaded = json.load(f)
            
            assert "alpha" in loaded
            assert "n_tests" in loaded
            assert "results" in loaded
            assert len(loaded["results"]) == len(p_values)
            
            # Verify structure of results
            for item in loaded["results"]:
                assert "original_p" in item
                assert "adjusted_p" in item
                assert "significant" in item

    def test_bonferroni_integration_with_anova_context(self):
        """
        Test Bonferroni correction in a context simulating post-hoc ANOVA comparisons.
        This ensures the correction works correctly when applied to pairwise p-values.
        """
        # Simulate 6 pairwise comparisons from a 4-level within-subjects factor
        # (4 choose 2 = 6 comparisons)
        simulated_pairwise_pvalues = [0.002, 0.015, 0.048, 0.120, 0.350, 0.890]
        alpha = 0.05
        
        corrected = apply_bonferroni_correction(simulated_pairwise_pvalues, alpha)
        
        n = len(simulated_pairwise_pvalues)
        
        # Verify all adjusted p-values are p * n, capped at 1.0
        for i, item in enumerate(corrected):
            expected_adj = min(simulated_pairwise_pvalues[i] * n, 1.0)
            assert abs(item["adjusted_p"] - expected_adj) < 1e-9
            
            # Verify significance logic
            expected_sig = expected_adj < alpha
            assert item["significant"] == expected_sig

        # Specifically check the borderline case: 0.048 * 6 = 0.288 (not significant)
        # Before correction it was < 0.05, after it is > 0.05
        borderline_idx = 2
        assert simulated_pairwise_pvalues[borderline_idx] < alpha
        assert corrected[borderline_idx]["significant"] is False

    def test_bonferroni_alpha_boundary(self):
        """Test behavior when adjusted p-value exactly equals alpha."""
        # If p * n == alpha, it should be False (strict inequality < alpha)
        # e.g., alpha=0.05, n=5, p=0.01 -> 0.05
        p_values = [0.01]
        alpha = 0.05
        n_tests = 5  # Simulating 5 comparisons
        
        corrected = apply_bonferroni_correction(p_values, alpha)
        
        assert abs(corrected[0]["adjusted_p"] - 0.05) < 1e-9
        assert corrected[0]["significant"] is False  # 0.05 is not < 0.05