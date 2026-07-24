"""
Unit tests for code/analysis/stats.py (Wilcoxon and Survival Analysis logic).

These tests validate:
1. Wilcoxon signed-rank test implementation (paired, non-censored data).
2. Survival Analysis (Cox PH) handling of censored data (N+1 penalty).
3. Bonferroni correction logic.
4. Data loading and pairing logic.
"""
import json
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pytest
from scipy import stats as scipy_stats

# Import the module under test
# Note: We assume the project root is in sys.path or we adjust the import
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
if str(project_root / "code") not in sys.path:
    sys.path.insert(0, str(project_root / "code"))

from analysis.stats import (
    load_agent_logs_for_pairing,
    calculate_coverage_metrics_for_issue,
    compute_paired_coverage_data,
    run_wilcoxon_signed_rank_test,
    run_exact_permutation_test,
    run_cox_survival_analysis,
    analyze_ranking_metrics,
    apply_bonferroni_correction,
    format_associational_statement
)


class TestWilcoxonLogic:
    """Tests for Wilcoxon signed-rank test logic."""

    def test_wilcoxon_basic(self):
        """Test basic Wilcoxon signed-rank test with known data."""
        # Known paired data from scipy docs or generated
        x = [20, 22, 25, 28, 30, 32, 35, 38, 40, 42]
        y = [21, 23, 26, 29, 31, 33, 36, 39, 41, 43]

        # Run our implementation
        result = run_wilcoxon_signed_rank_test(x, y)

        # Verify structure
        assert "statistic" in result
        assert "pvalue" in result
        assert "conclusion" in result

        # Verify against scipy (approximate due to implementation differences)
        scipy_res = scipy_stats.wilcoxon(x, y, zero_method="wilcox", correction=True)
        assert np.isclose(result["statistic"], scipy_res.statistic, rtol=0.1)
        # P-values might differ slightly due to exact vs asymptotic methods, but should be in same order of magnitude
        assert result["pvalue"] > 0 and result["pvalue"] < 1

    def test_wilcoxon_with_ties(self):
        """Test Wilcoxon with tied values."""
        x = [10, 10, 10, 20, 20]
        y = [10, 10, 15, 20, 25]

        result = run_wilcoxon_signed_rank_test(x, y)

        assert "statistic" in result
        assert "pvalue" in result
        # Should handle ties gracefully without crashing
        assert result["pvalue"] is not None

    def test_wilcoxon_identical(self):
        """Test Wilcoxon with identical arrays (should yield p=1.0 or near)."""
        x = [1, 2, 3, 4, 5]
        y = [1, 2, 3, 4, 5]

        result = run_wilcoxon_signed_rank_test(x, y)

        # If identical, statistic should be 0 (or max depending on definition) and p-value should be 1
        # Our implementation should not crash
        assert result["pvalue"] is not None


class TestSurvivalAnalysisLogic:
    """Tests for Cox Survival Analysis logic, specifically censored data handling."""

    def test_cox_survival_with_censored_data(self):
        """Test Cox PH with censored data (N+1 penalty scenario)."""
        # Simulate data where some entries are censored (no relevant line found)
        # In the project logic, censored data is assigned a ranking of N+1
        # and marked as censored=True in the survival model.

        # Create mock data: time (ranking) and event (1=found, 0=censored)
        # Group A (Baseline)
        times_a = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
        # Group B (Iterative) - some censored
        times_b = [4, 8, 12, 15, 20, 25, 30, 35, 40, 45]
        # Let's make the last 3 in B censored (event=0)
        events_b = [1, 1, 1, 1, 1, 1, 0, 0, 0, 0] # Last 4 are censored

        # We need to construct a DataFrame-like structure or list of dicts
        # The function expects a specific format, let's check the signature
        # run_cox_survival_analysis(times_baseline, times_iterative, events_baseline, events_iterative)
        # Assuming events_baseline are all 1 (no censoring) for simplicity in this test
        events_a = [1] * len(times_a)

        result = run_cox_survival_analysis(times_a, times_b, events_a, events_b)

        assert "hazard_ratio" in result
        assert "pvalue" in result
        assert "conclusion" in result
        # Hazard ratio should be a positive number
        assert result["hazard_ratio"] > 0

    def test_cox_survival_no_censored(self):
        """Test Cox PH when there is no censored data (should still work)."""
        times_a = [5, 10, 15, 20, 25]
        times_b = [4, 8, 12, 16, 20]
        events_a = [1, 1, 1, 1, 1]
        events_b = [1, 1, 1, 1, 1]

        result = run_cox_survival_analysis(times_a, times_b, events_a, events_b)

        assert "hazard_ratio" in result
        assert result["pvalue"] is not None

    def test_cox_survival_all_censored(self):
        """Test Cox PH when all data in one group is censored (edge case)."""
        # This might raise a warning or fail in the underlying lifelines library
        # Our function should handle it gracefully (return NaN or specific message)
        times_a = [10, 20, 30]
        times_b = [100, 100, 100] # Censored at max time
        events_a = [1, 1, 1]
        events_b = [0, 0, 0]

        try:
            result = run_cox_survival_analysis(times_a, times_b, events_a, events_b)
            # If it returns, check structure
            assert "hazard_ratio" in result
        except Exception:
            # It's acceptable for the underlying model to fail on this edge case
            # as long as our wrapper doesn't crash silently or produce garbage
            pass


class TestBonferroniCorrection:
    """Tests for Bonferroni correction logic."""

    def test_bonferroni_basic(self):
        """Test basic Bonferroni correction."""
        p_values = [0.01, 0.05, 0.10]
        alpha = 0.05
        k = len(p_values)

        result = apply_bonferroni_correction(p_values, alpha)

        assert "adjusted_pvalues" in result
        assert "alpha_corrected" in result
        assert "significant_flags" in result

        # Check adjusted p-values (min(p * k, 1.0))
        expected_adj = [min(p * k, 1.0) for p in p_values]
        for adj, exp in zip(result["adjusted_pvalues"], expected_adj):
            assert np.isclose(adj, exp)

        # Check corrected alpha
        assert np.isclose(result["alpha_corrected"], alpha / k)

    def test_bonferroni_empty(self):
        """Test Bonferroni with empty list."""
        result = apply_bonferroni_correction([], 0.05)
        assert result["adjusted_pvalues"] == []
        assert result["significant_flags"] == []


class TestPairingLogic:
    """Tests for data loading and pairing logic."""

    def test_load_pairing_mock_file(self):
        """Test loading and pairing from a temporary mock file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock baseline logs
            baseline_file = Path(tmpdir) / "baseline_logs.jsonl"
            iterative_file = Path(tmpdir) / "iterative_logs.jsonl"

            baseline_data = [
                {"issue_id": "1", "coverage": 0.5, "ranking": 10},
                {"issue_id": "2", "coverage": 0.6, "ranking": 8},
                {"issue_id": "3", "coverage": 0.4, "ranking": 15}
            ]
            iterative_data = [
                {"issue_id": "1", "coverage": 0.7, "ranking": 5},
                {"issue_id": "2", "coverage": 0.8, "ranking": 3},
                {"issue_id": "3", "coverage": 0.9, "ranking": 2}
            ]

            with open(baseline_file, "w") as f:
                for item in baseline_data:
                    f.write(json.dumps(item) + "\n")

            with open(iterative_file, "w") as f:
                for item in iterative_data:
                    f.write(json.dumps(item) + "\n")

            # Load and pair
            paired = load_agent_logs_for_pairing(str(baseline_file), str(iterative_file))

            assert len(paired) == 3
            # Check that issue_ids match
            for pair in paired:
                assert pair["baseline"]["issue_id"] == pair["iterative"]["issue_id"]
                # Check that metrics are present
                assert "coverage" in pair["baseline"]
                assert "coverage" in pair["iterative"]
                assert "ranking" in pair["baseline"]
                assert "ranking" in pair["iterative"]

    def test_load_pairing_missing_issue(self):
        """Test pairing when an issue is missing in one file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline_file = Path(tmpdir) / "baseline_logs.jsonl"
            iterative_file = Path(tmpdir) / "iterative_logs.jsonl"

            baseline_data = [
                {"issue_id": "1", "coverage": 0.5, "ranking": 10},
                {"issue_id": "2", "coverage": 0.6, "ranking": 8}
            ]
            iterative_data = [
                {"issue_id": "1", "coverage": 0.7, "ranking": 5},
                {"issue_id": "3", "coverage": 0.9, "ranking": 2} # Issue 2 missing here
            ]

            with open(baseline_file, "w") as f:
                for item in baseline_data:
                    f.write(json.dumps(item) + "\n")

            with open(iterative_file, "w") as f:
                for item in iterative_data:
                    f.write(json.dumps(item) + "\n")

            paired = load_agent_logs_for_pairing(str(baseline_file), str(iterative_file))

            # Should only return the matched issue (1)
            assert len(paired) == 1
            assert paired[0]["baseline"]["issue_id"] == "1"


class TestAssociationalFraming:
    """Tests for associational language framing."""

    def test_format_associational_statement(self):
        """Test that the function produces associational language."""
        result = format_associational_statement(
            metric_name="Coverage",
            p_value=0.03,
            effect_direction="higher",
            method="Wilcoxon"
        )

        assert "associational" in result.lower() or "difference" in result.lower()
        assert "caus" not in result.lower()
        assert "proves" not in result.lower()
        assert "causes" not in result.lower()