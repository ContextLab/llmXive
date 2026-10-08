"""
Unit tests for statistical analysis logic in code/analysis/statistics.py.

This module tests:
- Effect size calculation (Cohen's h for proportions)
- Power analysis for two-proportion tests
- Two-proportion Z-test
- Fisher's Exact Test
- Test selection logic based on expected cell counts
"""

import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pytest
from scipy import stats

# Import the module under test
# Adjust import path based on project structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from analysis.statistics import (
    StudyInvalidError,
    calculate_effect_size,
    power_analysis_two_proportions,
    two_proportion_z_test,
    fisher_exact_test,
    select_statistical_test,
    load_evaluation_results,
    aggregate_violation_rates,
)


class TestCalculateEffectSize:
    """Tests for calculate_effect_size function."""

    def test_cohen_h_identical_proportions(self):
        """Effect size should be 0 when proportions are identical."""
        p1, p2 = 0.5, 0.5
        effect_size = calculate_effect_size(p1, p2)
        assert math.isclose(effect_size, 0.0, abs_tol=1e-9)

    def test_cohen_h_small_difference(self):
        """Verify effect size calculation for small differences."""
        p1, p2 = 0.5, 0.55
        effect_size = calculate_effect_size(p1, p2)
        # Cohen's h = 2 * arcsin(sqrt(p1)) - 2 * arcsin(sqrt(p2))
        expected = 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))
        assert math.isclose(effect_size, expected, abs_tol=1e-6)

    def test_cohen_h_large_difference(self):
        """Verify effect size for large differences."""
        p1, p2 = 0.1, 0.9
        effect_size = calculate_effect_size(p1, p2)
        expected = 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))
        assert math.isclose(abs(effect_size), abs(expected), abs_tol=1e-6)

    def test_cohen_h_edge_case_zero(self):
        """Effect size when one proportion is 0."""
        p1, p2 = 0.0, 0.5
        effect_size = calculate_effect_size(p1, p2)
        expected = 2 * math.asin(math.sqrt(0.0)) - 2 * math.asin(math.sqrt(0.5))
        assert math.isclose(effect_size, expected, abs_tol=1e-6)

    def test_cohen_h_edge_case_one(self):
        """Effect size when one proportion is 1."""
        p1, p2 = 1.0, 0.5
        effect_size = calculate_effect_size(p1, p2)
        expected = 2 * math.asin(math.sqrt(1.0)) - 2 * math.asin(math.sqrt(0.5))
        assert math.isclose(effect_size, expected, abs_tol=1e-6)

    def test_invalid_proportions_negative(self):
        """Should raise ValueError for negative proportions."""
        with pytest.raises(ValueError):
            calculate_effect_size(-0.1, 0.5)

    def test_invalid_proportions_greater_than_one(self):
        """Should raise ValueError for proportions > 1."""
        with pytest.raises(ValueError):
            calculate_effect_size(0.5, 1.5)


class TestPowerAnalysisTwoProportions:
    """Tests for power_analysis_two_proportions function."""

    def test_power_analysis_basic(self):
        """Basic power analysis with standard parameters."""
        result = power_analysis_two_proportions(
            p1=0.5, p2=0.6, n1=100, n2=100, alpha=0.05
        )
        assert "power" in result
        assert "effect_size" in result
        assert "sample_size_total" in result
        assert 0 <= result["power"] <= 1

    def test_power_increases_with_sample_size(self):
        """Power should increase as sample size increases."""
        result_small = power_analysis_two_proportions(
            p1=0.5, p2=0.6, n1=50, n2=50, alpha=0.05
        )
        result_large = power_analysis_two_proportions(
            p1=0.5, p2=0.6, n1=200, n2=200, alpha=0.05
        )
        assert result_large["power"] > result_small["power"]

    def test_power_increases_with_effect_size(self):
        """Power should increase as effect size increases."""
        result_small = power_analysis_two_proportions(
            p1=0.5, p2=0.55, n1=100, n2=100, alpha=0.05
        )
        result_large = power_analysis_two_proportions(
            p1=0.5, p2=0.7, n1=100, n2=100, alpha=0.05
        )
        assert result_large["power"] > result_small["power"]

    def test_power_decreases_with_stricter_alpha(self):
        """Power should decrease with smaller alpha."""
        result_alpha_05 = power_analysis_two_proportions(
            p1=0.5, p2=0.6, n1=100, n2=100, alpha=0.05
        )
        result_alpha_01 = power_analysis_two_proportions(
            p1=0.5, p2=0.6, n1=100, n2=100, alpha=0.01
        )
        assert result_alpha_01["power"] < result_alpha_05["power"]

    def test_power_target_met(self):
        """Verify power meets target when sample size is sufficient."""
        result = power_analysis_two_proportions(
            p1=0.5, p2=0.8, n1=100, n2=100, alpha=0.05
        )
        # With large effect size, power should be high
        assert result["power"] > 0.8

    def test_power_not_met_small_sample(self):
        """Verify power is low when sample size is insufficient."""
        result = power_analysis_two_proportions(
            p1=0.5, p2=0.51, n1=20, n2=20, alpha=0.05
        )
        # With small effect size and small sample, power should be low
        assert result["power"] < 0.5


class TestTwoProportionZTest:
    """Tests for two_proportion_z_test function."""

    def test_z_test_identical_proportions(self):
        """Z-test should yield high p-value for identical proportions."""
        # 50 successes out of 100 for both groups
        result = two_proportion_z_test(
            successes1=50, n1=100, successes2=50, n2=100
        )
        assert math.isclose(result["p_value"], 1.0, abs_tol=0.01)

    def test_z_test_different_proportions(self):
        """Z-test should yield low p-value for different proportions."""
        # Group 1: 50/100, Group 2: 80/100 (large difference)
        result = two_proportion_z_test(
            successes1=50, n1=100, successes2=80, n2=100
        )
        assert result["p_value"] < 0.001

    def test_z_test_one_sided(self):
        """Test one-sided alternative hypothesis."""
        result = two_proportion_z_test(
            successes1=50, n1=100, successes2=80, n2=100, alternative="less"
        )
        # Group 1 < Group 2, so one-sided p-value should be very small
        assert result["p_value"] < 0.001

    def test_z_test_two_sided(self):
        """Test two-sided alternative hypothesis."""
        result = two_proportion_z_test(
            successes1=50, n1=100, successes2=80, n2=100, alternative="two-sided"
        )
        assert result["p_value"] < 0.001

    def test_z_test_greater(self):
        """Test greater alternative hypothesis."""
        # Group 1 > Group 2
        result = two_proportion_z_test(
            successes1=80, n1=100, successes2=50, n2=100, alternative="greater"
        )
        assert result["p_value"] < 0.001

    def test_z_test_edge_case_zero_successes(self):
        """Test with zero successes in one group."""
        result = two_proportion_z_test(
            successes1=0, n1=100, successes2=50, n2=100
        )
        assert result["p_value"] < 0.001

    def test_z_test_edge_case_all_successes(self):
        """Test with all successes in one group."""
        result = two_proportion_z_test(
            successes1=100, n1=100, successes2=50, n2=100
        )
        assert result["p_value"] < 0.001

    def test_invalid_sample_size_zero(self):
        """Should raise ValueError for zero sample size."""
        with pytest.raises(ValueError):
            two_proportion_z_test(successes1=10, n1=0, successes2=10, n2=100)

    def test_invalid_successes_greater_than_n(self):
        """Should raise ValueError if successes > n."""
        with pytest.raises(ValueError):
            two_proportion_z_test(successes1=110, n1=100, successes2=50, n2=100)


class TestFisherExactTest:
    """Tests for fisher_exact_test function."""

    def test_fisher_identical_proportions(self):
        """Fisher's test should yield high p-value for identical proportions."""
        # 50 successes out of 100 for both groups
        result = fisher_exact_test(
            successes1=50, n1=100, failures1=50, successes2=50, n2=100, failures2=50
        )
        assert result["p_value"] > 0.5

    def test_fisher_different_proportions(self):
        """Fisher's test should yield low p-value for different proportions."""
        # Group 1: 20/100, Group 2: 80/100 (large difference)
        result = fisher_exact_test(
            successes1=20, n1=100, failures1=80, successes2=80, n2=100, failures2=20
        )
        assert result["p_value"] < 0.001

    def test_fisher_one_sided_less(self):
        """Test one-sided 'less' alternative."""
        result = fisher_exact_test(
            successes1=20, n1=100, failures1=80, successes2=80, n2=100, failures2=20,
            alternative="less"
        )
        assert result["p_value"] < 0.001

    def test_fisher_one_sided_greater(self):
        """Test one-sided 'greater' alternative."""
        result = fisher_exact_test(
            successes1=80, n1=100, failures1=20, successes2=20, n2=100, failures2=80,
            alternative="greater"
        )
        assert result["p_value"] < 0.001

    def test_fisher_two_sided(self):
        """Test two-sided alternative."""
        result = fisher_exact_test(
            successes1=20, n1=100, failures1=80, successes2=80, n2=100, failures2=20,
            alternative="two-sided"
        )
        assert result["p_value"] < 0.001

    def test_fisher_small_sample_exact(self):
        """Test with small sample sizes where Fisher is preferred."""
        result = fisher_exact_test(
            successes1=1, n1=5, failures1=4, successes2=4, n2=5, failures2=1
        )
        assert 0 <= result["p_value"] <= 1

    def test_fisher_edge_case_zero_cell(self):
        """Test with a zero cell in contingency table."""
        result = fisher_exact_test(
            successes1=0, n1=10, failures1=10, successes2=10, n2=10, failures2=0
        )
        assert result["p_value"] == 0.0

    def test_invalid_failsures_negative(self):
        """Should raise ValueError for negative failures."""
        with pytest.raises(ValueError):
            fisher_exact_test(
                successes1=10, n1=10, failures1=-5,
                successes2=10, n2=10, failures2=10
            )

    def test_invalid_failsures_mismatch(self):
        """Should raise ValueError if failures != n - successes."""
        with pytest.raises(ValueError):
            fisher_exact_test(
                successes1=10, n1=10, failures1=5,  # 10 - 10 != 5
                successes2=10, n2=10, failures2=10
            )


class TestSelectStatisticalTest:
    """Tests for select_statistical_test function."""

    def test_select_z_test_large_cells(self):
        """Should select Z-test when all expected cells >= 5."""
        # Large sample, proportions ~0.5 -> expected cells ~50
        test_type, reason = select_statistical_test(
            successes1=50, n1=100, successes2=50, n2=100
        )
        assert test_type == "z_test"
        assert "expected cell counts" in reason.lower()

    def test_select_fisher_small_cells(self):
        """Should select Fisher's test when expected cells < 5."""
        # Small sample, low success rate -> expected cells < 5
        test_type, reason = select_statistical_test(
            successes1=1, n1=10, successes2=1, n2=10
        )
        assert test_type == "fisher_exact"
        assert "expected cell counts" in reason.lower()

    def test_select_fisher_very_small_sample(self):
        """Should select Fisher's test for very small samples."""
        test_type, reason = select_statistical_test(
            successes1=0, n1=3, successes2=1, n2=3
        )
        assert test_type == "fisher_exact"

    def test_select_z_test_balanced_large(self):
        """Z-test for balanced large samples."""
        test_type, reason = select_statistical_test(
            successes1=450, n1=1000, successes2=550, n2=1000
        )
        assert test_type == "z_test"


class TestLoadEvaluationResults:
    """Tests for load_evaluation_results function."""

    def test_load_single_result(self):
        """Load a single evaluation result file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result_path = Path(tmpdir) / "test_scene.json"
            data = {
                "scene_id": "test_scene",
                "violations": 2,
                "total_objects": 10,
                "violation_rate": 0.2
            }
            with open(result_path, "w") as f:
                json.dump(data, f)

            loaded = load_evaluation_results([str(result_path)])
            assert len(loaded) == 1
            assert loaded[0]["scene_id"] == "test_scene"

    def test_load_multiple_results(self):
        """Load multiple evaluation result files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results = []
            for i in range(3):
                result_path = Path(tmpdir) / f"scene_{i}.json"
                data = {
                    "scene_id": f"scene_{i}",
                    "violations": i,
                    "total_objects": 10,
                    "violation_rate": i / 10
                }
                with open(result_path, "w") as f:
                    json.dump(data, f)
                results.append(str(result_path))

            loaded = load_evaluation_results(results)
            assert len(loaded) == 3

    def test_load_nonexistent_file(self):
        """Should raise FileNotFoundError for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            load_evaluation_results(["/nonexistent/path.json"])

    def test_load_invalid_json(self):
        """Should raise JSONDecodeError for invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result_path = Path(tmpdir) / "invalid.json"
            with open(result_path, "w") as f:
                f.write("not valid json")

            with pytest.raises(json.JSONDecodeError):
                load_evaluation_results([str(result_path)])


class TestAggregateViolationRates:
    """Tests for aggregate_violation_rates function."""

    def test_aggregate_basic(self):
        """Basic aggregation of violation rates."""
        results = [
            {"scene_id": "1", "violations": 2, "total_objects": 10},
            {"scene_id": "2", "violations": 3, "total_objects": 10},
            {"scene_id": "3", "violations": 1, "total_objects": 10},
        ]
        agg = aggregate_violation_rates(results)
        assert agg["total_violations"] == 6
        assert agg["total_objects"] == 30
        assert math.isclose(agg["violation_rate"], 0.2, abs_tol=1e-6)

    def test_aggregate_empty(self):
        """Aggregation of empty list should return zeros."""
        agg = aggregate_violation_rates([])
        assert agg["total_violations"] == 0
        assert agg["total_objects"] == 0
        assert agg["violation_rate"] == 0.0

    def test_aggregate_single(self):
        """Aggregation of single result."""
        results = [
            {"scene_id": "1", "violations": 5, "total_objects": 20},
        ]
        agg = aggregate_violation_rates(results)
        assert agg["total_violations"] == 5
        assert agg["total_objects"] == 20
        assert math.isclose(agg["violation_rate"], 0.25, abs_tol=1e-6)

    def test_aggregate_zero_violations(self):
        """Aggregation with zero violations."""
        results = [
            {"scene_id": "1", "violations": 0, "total_objects": 10},
            {"scene_id": "2", "violations": 0, "total_objects": 10},
        ]
        agg = aggregate_violation_rates(results)
        assert agg["violation_rate"] == 0.0

    def test_aggregate_all_violations(self):
        """Aggregation where all objects violate."""
        results = [
            {"scene_id": "1", "violations": 10, "total_objects": 10},
            {"scene_id": "2", "violations": 5, "total_objects": 5},
        ]
        agg = aggregate_violation_rates(results)
        assert math.isclose(agg["violation_rate"], 1.0, abs_tol=1e-6)


class TestStudyInvalidError:
    """Tests for StudyInvalidError exception."""

    def test_study_invalid_error_creation(self):
        """Verify StudyInvalidError can be created with message."""
        error = StudyInvalidError("Study invalid due to high contradiction rate")
        assert str(error) == "Study invalid due to high contradiction rate"

    def test_study_invalid_error_inheritance(self):
        """Verify StudyInvalidError is a subclass of Exception."""
        assert issubclass(StudyInvalidError, Exception)

    def test_study_invalid_error_raised(self):
        """Verify StudyInvalidError can be raised and caught."""
        with pytest.raises(StudyInvalidError):
            raise StudyInvalidError("Test error")