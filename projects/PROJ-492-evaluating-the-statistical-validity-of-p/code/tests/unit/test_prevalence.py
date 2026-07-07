"""
Unit tests for prevalence analysis module (T042).
Tests binomial test, Wilson CI, sensitivity analysis, and Bonferroni correction.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
from scipy import stats

from code.src.audit.prevalence import (
    binomial_test,
    wilson_ci,
    compute_prevalence,
    sensitivity_analysis,
    apply_dynamic_bonferroni,
    load_audit_records,
    write_prevalence_results,
    run_prevalence_analysis,
    set_rng_seed_for_prevalence
)


class TestBinomialTest:
    """Tests for the binomial_test function."""

    def test_binomial_test_expected(self):
        """Test binomial test with known values."""
        # 50 successes out of 100 with p0=0.5 should give p-value ~1.0
        p_val = binomial_test(50, 100, 0.5)
        assert 0.9 < p_val <= 1.0, f"Expected p-value near 1.0, got {p_val}"

    def test_binomial_test_significant(self):
        """Test binomial test with significant deviation."""
        # 90 successes out of 100 with p0=0.5 should be significant
        p_val = binomial_test(90, 100, 0.5)
        assert p_val < 0.001, f"Expected significant p-value, got {p_val}"

    def test_binomial_test_edge_cases(self):
        """Test edge cases: n=0, invalid successes."""
        assert binomial_test(0, 0, 0.5) == 1.0
        assert binomial_test(-1, 10, 0.5) == 1.0
        assert binomial_test(11, 10, 0.5) == 1.0


class TestWilsonCI:
    """Tests for the wilson_ci function."""

    def test_wilson_ci_symmetry(self):
        """Wilson CI should be symmetric around p=0.5 for large n."""
        lower, upper = wilson_ci(500, 1000, 0.05)
        assert abs((lower + upper) / 2 - 0.5) < 0.01

    def test_wilson_ci_width(self):
        """CI width should decrease as n increases."""
        lower1, upper1 = wilson_ci(50, 100, 0.05)
        lower2, upper2 = wilson_ci(500, 1000, 0.05)
        width1 = upper1 - lower1
        width2 = upper2 - lower2
        assert width2 < width1, f"CI should narrow with larger n: {width2} vs {width1}"

    def test_wilson_ci_bounds(self):
        """CI bounds should be within [0, 1]."""
        lower, upper = wilson_ci(0, 100, 0.05)
        assert 0.0 <= lower <= upper <= 1.0

    def test_wilson_ci_edge_cases(self):
        """Test edge cases: n=0, all successes, all failures."""
        lower, upper = wilson_ci(0, 0, 0.05)
        assert lower == 0.0 and upper == 0.0

        lower, upper = wilson_ci(100, 100, 0.05)
        assert lower > 0.9 and upper == 1.0


class TestComputePrevalence:
    """Tests for compute_prevalence function."""

    def test_compute_prevalence_empty(self):
        """Prevalence on empty list."""
        result = compute_prevalence([])
        assert result["total_summaries"] == 0
        assert result["inconsistent_count"] == 0
        assert result["inconsistent_rate"] == 0.0

    def test_compute_prevalence_all_inconsistent(self):
        """Prevalence when all are inconsistent."""
        records = [{"is_inconsistent": True} for _ in range(10)]
        result = compute_prevalence(records)
        assert result["inconsistent_count"] == 10
        assert result["inconsistent_rate"] == 1.0

    def test_compute_prevalence_none_inconsistent(self):
        """Prevalence when none are inconsistent."""
        records = [{"is_inconsistent": False} for _ in range(10)]
        result = compute_prevalence(records)
        assert result["inconsistent_count"] == 0
        assert result["inconsistent_rate"] == 0.0

    def test_compute_prevalence_ci_width(self):
        """CI width check for known rate."""
        records = [{"is_inconsistent": True} for _ in range(180)] + \
                  [{"is_inconsistent": False} for _ in range(20)]
        result = compute_prevalence(records)
        # Rate should be 0.9
        assert abs(result["inconsistent_rate"] - 0.9) < 0.01
        # CI width should be <= 0.10 (per task requirement)
        width = result["wilson_ci_upper"] - result["wilson_ci_lower"]
        assert width <= 0.10, f"CI width {width} exceeds 0.10"


class TestSensitivityAnalysis:
    """Tests for sensitivity_analysis function."""

    def test_sensitivity_analysis_variation(self):
        """Sensitivity analysis should compute variation across thresholds."""
        records = [{"p_value_difference": 0.03} for _ in range(100)]
        result = sensitivity_analysis(records, [0.01, 0.05, 0.10])

        assert "results" in result
        assert "max_variation" in result
        assert result["max_variation_acceptable"] is True  # Variation < 0.02

    def test_sensitivity_analysis_empty(self):
        """Sensitivity on empty list."""
        result = sensitivity_analysis([])
        assert result["max_variation"] == 0.0

    def test_sensitivity_analysis_default_range(self):
        """Default baseline range is used if not provided."""
        records = [{"p_value_difference": 0.05} for _ in range(10)]
        result = sensitivity_analysis(records)
        assert 0.01 in result["thresholds_tested"]
        assert 0.05 in result["thresholds_tested"]


class TestBonferroni:
    """Tests for dynamic Bonferroni correction."""

    def test_bonferroni_single_group(self):
        """No correction for single group."""
        alpha = apply_dynamic_bonferroni(1)
        assert alpha == 0.05

    def test_bonferroni_multiple_groups(self):
        """Correction applied for multiple groups."""
        alpha = apply_dynamic_bonferroni(5)
        assert abs(alpha - 0.01) < 1e-6

    def test_bonferroni_invalid_groups(self):
        """Handle invalid group count."""
        alpha = apply_dynamic_bonferroni(0)
        assert alpha == 0.05


class TestLoadAndWrite:
    """Tests for load_audit_records and write_prevalence_results."""

    def test_load_audit_records_list(self, tmp_path):
        """Load records from JSON list."""
        data = [{"id": 1, "is_inconsistent": True}]
        input_file = tmp_path / "test.json"
        input_file.write_text(json.dumps(data))

        records = load_audit_records(input_file)
        assert len(records) == 1
        assert records[0]["id"] == 1

    def test_load_audit_records_dict(self, tmp_path):
        """Load records from JSON dict with 'records' key."""
        data = {"records": [{"id": 1}, {"id": 2}]}
        input_file = tmp_path / "test.json"
        input_file.write_text(json.dumps(data))

        records = load_audit_records(input_file)
        assert len(records) == 2

    def test_write_prevalence_results(self, tmp_path):
        """Write results to JSON file."""
        output_file = tmp_path / "prevalence.json"
        prevalence = {"total_summaries": 100, "inconsistent_count": 10}
        sensitivity = {"results": {}, "max_variation": 0.01}

        write_prevalence_results(output_file, prevalence, sensitivity, 0.025)

        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
        assert "prevalence" in data
        assert "sensitivity_analysis" in data
        assert data["dynamic_bonferroni_alpha"] == 0.025


class TestRunPrevalenceAnalysis:
    """Integration test for run_prevalence_analysis."""

    def test_run_prevalence_analysis_full(self, tmp_path):
        """Run full pipeline on mock data."""
        input_file = tmp_path / "audit_report.json"
        output_file = tmp_path / "prevalence.json"

        records = [
            {"is_inconsistent": True, "p_value_difference": 0.06},
            {"is_inconsistent": False, "p_value_difference": 0.01},
            {"is_inconsistent": True, "p_value_difference": 0.08}
        ]
        input_file.write_text(json.dumps(records))

        result = run_prevalence_analysis(input_file, output_file, num_subgroups=3)

        assert output_file.exists()
        assert result["prevalence"]["inconsistent_count"] == 2
        assert result["prevalence"]["total_summaries"] == 3
        assert abs(result["bonferroni_alpha"] - 0.01666) < 1e-4

        # Verify JSON content
        with open(output_file) as f:
            data = json.load(f)
        assert "generated_at" in data
        assert "sensitivity_analysis" in data
        assert "dynamic_bonferroni_alpha" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])