"""
Unit tests for code/analysis/stats.py.

This module validates the statistical logic for Wilcoxon signed-rank tests,
Exact Permutation tests, and Survival Analysis (Cox PH) including censored data handling.
"""
import json
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from analysis.stats import (
    run_wilcoxon_signed_rank_test,
    run_exact_permutation_test,
    run_cox_survival_analysis,
    apply_bonferroni_correction,
    load_agent_logs_for_pairing,
    compute_paired_coverage_data
)


class TestWilcoxonSignedRank:
    """Tests for the Wilcoxon signed-rank test implementation."""

    def test_wilcoxon_identical_pairs(self):
        """Test with identical pairs (should result in W=0 or non-significant)."""
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        stat, pval = run_wilcoxon_signed_rank_test(x, y)
        
        # With identical pairs, statistic should be 0 or very low
        assert stat == 0.0
        assert pval == 1.0  # Perfectly correlated, no difference

    def test_wilcoxon_significant_difference(self):
        """Test with a clear systematic difference."""
        # Baseline is consistently lower than Iterative
        baseline = [10.0, 12.0, 11.0, 13.0, 10.5]
        iterative = [20.0, 22.0, 21.0, 23.0, 20.5]
        
        stat, pval = run_wilcoxon_signed_rank_test(baseline, iterative)
        
        assert stat > 0
        assert pval < 0.05  # Should be significant given the clear gap

    def test_wilcoxon_small_sample(self):
        """Test with small sample size (N=3)."""
        x = [1.0, 2.0, 3.0]
        y = [2.0, 3.0, 4.0]
        
        # Should not raise an error even with small N
        stat, pval = run_wilcoxon_signed_rank_test(x, y)
        
        assert isinstance(stat, float)
        assert isinstance(pval, float)
        assert 0.0 <= pval <= 1.0

    def test_wilcoxon_ties_handling(self):
        """Test that ties are handled correctly (continuity correction)."""
        # Create data with ties
        x = [1.0, 1.0, 2.0, 2.0, 3.0]
        y = [1.5, 1.5, 2.5, 2.5, 3.5]
        
        stat, pval = run_wilcoxon_signed_rank_test(x, y)
        
        assert isinstance(stat, float)
        assert isinstance(pval, float)
        # Ties should not cause NaN or Inf
        assert not np.isnan(stat)
        assert not np.isinf(stat)


class TestExactPermutation:
    """Tests for the Exact Permutation test implementation."""

    def test_permutation_identical(self):
        """Test with identical data (p-value should be 1.0)."""
        x = [1.0, 2.0, 3.0, 4.0]
        y = [1.0, 2.0, 3.0, 4.0]
        
        stat, pval = run_exact_permutation_test(x, y)
        
        assert pval == 1.0

    def test_permutation_significant(self):
        """Test with clearly separated groups."""
        x = [1.0, 1.1, 1.2, 1.3]
        y = [10.0, 10.1, 10.2, 10.3]
        
        stat, pval = run_exact_permutation_test(x, y)
        
        # With perfect separation, p-value should be very low
        assert pval < 0.05

    def test_permutation_single_pair(self):
        """Test with minimal sample size (N=1)."""
        x = [1.0]
        y = [2.0]
        
        # Should handle N=1 gracefully
        stat, pval = run_exact_permutation_test(x, y)
        
        assert isinstance(pval, float)

    def test_permutation_ties_heavy(self):
        """Test with many ties (dominant ties scenario)."""
        # Many identical values
        x = [0.0, 0.0, 0.0, 0.0, 0.0]
        y = [0.0, 0.0, 0.0, 0.0, 0.1]
        
        stat, pval = run_exact_permutation_test(x, y)
        
        assert not np.isnan(pval)
        assert 0.0 <= pval <= 1.0


class TestSurvivalAnalysis:
    """Tests for Survival Analysis (Cox PH) with censored data."""

    def test_cox_no_censoring(self):
        """Test Cox model with no censored data (all events observed)."""
        # Create synthetic data: time, event (1=event, 0=censored), group
        # Simulating 'baseline' vs 'iterative' groups
        times = np.array([10.0, 12.0, 15.0, 20.0, 25.0])
        events = np.array([1, 1, 1, 1, 1])  # All observed
        group = np.array([0, 0, 1, 1, 1])  # 0=baseline, 1=iterative
        
        # Create DataFrame-like structure expected by lifelines
        df = {
            'T': times,
            'E': events,
            'group': group
        }
        
        hazard_ratio, pval = run_cox_survival_analysis(df)
        
        assert hazard_ratio is not None
        assert isinstance(pval, float)
        assert 0.0 <= pval <= 1.0

    def test_cox_with_censoring(self):
        """Test Cox model with censored data (crucial for ranking efficiency)."""
        # Simulate censored data: some issues never found the solution
        times = np.array([5.0, 8.0, 12.0, 20.0, 30.0])
        events = np.array([1, 0, 1, 0, 1])  # 0 = censored (N+1 penalty logic)
        group = np.array([0, 0, 1, 1, 1])
        
        df = {
            'T': times,
            'E': events,
            'group': group
        }
        
        hazard_ratio, pval = run_cox_survival_analysis(df)
        
        # Should handle censoring without crashing
        assert hazard_ratio is not None
        assert isinstance(pval, float)
        assert not np.isnan(hazard_ratio)

    def test_cox_all_censored(self):
        """Test edge case: all data censored (should handle gracefully)."""
        times = np.array([10.0, 20.0, 30.0])
        events = np.array([0, 0, 0])  # All censored
        group = np.array([0, 1, 0])
        
        df = {
            'T': times,
            'E': events,
            'group': group
        }
        
        # Should not crash, might return NaN or specific warning
        hazard_ratio, pval = run_cox_survival_analysis(df)
        
        # The function should handle this gracefully (return NaN or similar)
        # We assert it doesn't crash and returns a float-like
        assert isinstance(pval, float)

    def test_cox_group_imbalance(self):
        """Test with highly imbalanced group sizes."""
        times = np.array([5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 20.0])
        events = np.array([1, 1, 1, 1, 1, 1, 1])
        group = np.array([0, 0, 0, 0, 0, 0, 1])  # 6 vs 1
        
        df = {
            'T': times,
            'E': events,
            'group': group
        }
        
        hazard_ratio, pval = run_cox_survival_analysis(df)
        
        assert isinstance(pval, float)


class TestBonferroniCorrection:
    """Tests for Bonferroni correction logic."""

    def test_bonferroni_simple(self):
        """Test basic Bonferroni correction."""
        p_values = [0.01, 0.05, 0.10]
        alpha = 0.05
        
        adjusted = apply_bonferroni_correction(p_values, alpha)
        
        assert len(adjusted) == len(p_values)
        # Adjusted p-values should be >= original
        for adj, orig in zip(adjusted, p_values):
            assert adj >= orig
        
        # First one (0.01 * 3 = 0.03) should be < 0.05
        assert adjusted[0] < 0.05
        # Second one (0.05 * 3 = 0.15) should be > 0.05
        assert adjusted[1] > 0.05

    def test_bonferroni_cap_at_1(self):
        """Test that adjusted p-values are capped at 1.0."""
        p_values = [0.5, 0.6, 0.7]
        alpha = 0.05
        
        adjusted = apply_bonferroni_correction(p_values, alpha)
        
        for adj in adjusted:
            assert adj <= 1.0

    def test_bonferroni_empty_list(self):
        """Test with empty list."""
        p_values = []
        alpha = 0.05
        
        adjusted = apply_bonferroni_correction(p_values, alpha)
        
        assert len(adjusted) == 0


class TestPairingLogic:
    """Tests for data loading and pairing logic."""

    def test_load_agent_logs_pairing(self, tmp_path):
        """Test that logs are correctly paired by issue_id."""
        # Create mock log files
        baseline_path = tmp_path / "baseline_logs.jsonl"
        iterative_path = tmp_path / "iterative_logs.jsonl"
        
        baseline_data = [
            {"issue_id": "1", "coverage": 0.5, "rank": 10},
            {"issue_id": "2", "coverage": 0.3, "rank": 20},
            {"issue_id": "3", "coverage": 0.8, "rank": 5}
        ]
        
        iterative_data = [
            {"issue_id": "1", "coverage": 0.7, "rank": 5},
            {"issue_id": "2", "coverage": 0.4, "rank": 15},
            {"issue_id": "3", "coverage": 0.9, "rank": 2}
        ]
        
        with open(baseline_path, "w") as f:
            for item in baseline_data:
                f.write(json.dumps(item) + "\n")
        
        with open(iterative_path, "w") as f:
            for item in iterative_data:
                f.write(json.dumps(item) + "\n")
        
        # Load and pair
        paired = load_agent_logs_for_pairing(str(baseline_path), str(iterative_path))
        
        assert len(paired) == 3
        # Check specific pairings
        assert paired[0]["issue_id"] == "1"
        assert paired[0]["baseline_coverage"] == 0.5
        assert paired[0]["iterative_coverage"] == 0.7

    def test_compute_paired_coverage_data(self, tmp_path):
        """Test coverage data computation from paired logs."""
        baseline_path = tmp_path / "baseline.jsonl"
        iterative_path = tmp_path / "iterative.jsonl"
        
        # Write test data
        with open(baseline_path, "w") as f:
            f.write(json.dumps({"issue_id": "1", "coverage": 0.5}) + "\n")
            f.write(json.dumps({"issue_id": "2", "coverage": 0.3}) + "\n")
        
        with open(iterative_path, "w") as f:
            f.write(json.dumps({"issue_id": "1", "coverage": 0.6}) + "\n")
            f.write(json.dumps({"issue_id": "2", "coverage": 0.4}) + "\n")
        
        baseline_arr, iterative_arr = compute_paired_coverage_data(
            str(baseline_path), str(iterative_path)
        )
        
        assert len(baseline_arr) == 2
        assert len(iterative_arr) == 2
        assert np.allclose(baseline_arr, [0.5, 0.3])
        assert np.allclose(iterative_arr, [0.6, 0.4])

    def test_paired_coverage_missing_issue(self, tmp_path):
        """Test behavior when an issue is missing from one log."""
        baseline_path = tmp_path / "baseline.jsonl"
        iterative_path = tmp_path / "iterative.jsonl"
        
        with open(baseline_path, "w") as f:
            f.write(json.dumps({"issue_id": "1", "coverage": 0.5}) + "\n")
            f.write(json.dumps({"issue_id": "2", "coverage": 0.3}) + "\n")
            f.write(json.dumps({"issue_id": "3", "coverage": 0.4}) + "\n")
        
        with open(iterative_path, "w") as f:
            f.write(json.dumps({"issue_id": "1", "coverage": 0.6}) + "\n")
            # Issue 2 is missing
            f.write(json.dumps({"issue_id": "3", "coverage": 0.5}) + "\n")
        
        baseline_arr, iterative_arr = compute_paired_coverage_data(
            str(baseline_path), str(iterative_path)
        )
        
        # Should only return pairs that exist in BOTH
        assert len(baseline_arr) == 2
        assert len(iterative_arr) == 2
        # Issue 1 and 3 should be present
        assert 0.5 in baseline_arr
        assert 0.4 in baseline_arr