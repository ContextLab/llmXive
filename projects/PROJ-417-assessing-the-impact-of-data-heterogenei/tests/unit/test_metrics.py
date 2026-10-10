"""Unit tests for the metrics calculation module (T004, FR-003)."""

import os
import sys
import pytest
from pathlib import Path

# Make the code package importable when running pytest from the
# project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from analysis.metrics import (
    MetricsResult,
    calculate_bias,
    calculate_coverage,
    calculate_i_squared,
    aggregate_metrics,
    compute_metrics_from_simulation,
)


class TestCalculateBias:
    def test_exact_match_gives_zero_bias(self):
        assert calculate_bias(0.5, 0.5) == 0.0

    def test_positive_bias(self):
        assert calculate_bias(0.7, 0.5) == pytest.approx(0.2)

    def test_negative_bias(self):
        assert calculate_bias(0.3, 0.5) == pytest.approx(-0.2)

class TestCalculateCoverage:
    def test_true_effect_inside_ci(self):
        assert calculate_coverage(0.2, 0.8, 0.5) is True

    def test_true_effect_on_lower_bound(self):
        assert calculate_coverage(0.5, 0.8, 0.5) is True

    def test_true_effect_on_upper_bound(self):
        assert calculate_coverage(0.2, 0.5, 0.5) is True

    def test_true_effect_below_ci(self):
        assert calculate_coverage(0.2, 0.8, 0.1) is False

    def test_true_effect_above_ci(self):
        assert calculate_coverage(0.2, 0.8, 0.9) is False

class TestExactEstimate:
    """Verification requirement: a pooled estimate exactly equal to the
    true effect results in zero bias and a coverage flag of True."""

    def test_exact_estimate_zero_bias_and_covered(self):
        records = [
            {
                "replicate_id": 0,
                "injected_true_effect": 0.5,
                "pooled_effect": 0.5,
                "ci_lower": 0.3,
                "ci_upper": 0.7,
                "tau_squared_estimate": 0.0,
                "i_squared": 0.0,
            }
        ]
        results = compute_metrics_from_simulation(records)
        assert len(results) == 1
        r = results[0]
        assert r.bias == 0.0
        assert r.coverage_flag is True

    def test_exact_estimate_at_ci_boundary_is_covered(self):
        # Even a degenerate CI centered exactly on the truth covers it.
        records = [
            {
                "replicate_id": 1,
                "injected_true_effect": 0.25,
                "pooled_effect": 0.25,
                "ci_lower": 0.25,
                "ci_upper": 0.25,
            }
        ]
        r = compute_metrics_from_simulation(records)[0]
        assert r.bias == 0.0
        assert r.coverage_flag is True

class TestTrueEffectColumnEnforced:
    def test_missing_injected_true_effect_raises(self):
        records = [
            {
                "replicate_id": 0,
                "true_effect": 0.5,  # wrong column name
                "pooled_effect": 0.5,
                "ci_lower": 0.3,
                "ci_upper": 0.7,
            }
        ]
        with pytest.raises(KeyError):
            compute_metrics_from_simulation(records)

    def test_non_numeric_true_effect_raises(self):
        records = [
            {
                "injected_true_effect": "not-a-number",
                "pooled_effect": 0.5,
                "ci_lower": 0.3,
                "ci_upper": 0.7,
            }
        ]
        with pytest.raises(ValueError):
            compute_metrics_from_simulation(records)

    def test_nan_true_effect_raises(self):
        records = [
            {
                "injected_true_effect": float("nan"),
                "pooled_effect": 0.5,
                "ci_lower": 0.3,
                "ci_upper": 0.7,
            }
        ]
        with pytest.raises(ValueError):
            compute_metrics_from_simulation(records)

    def test_missing_pooled_effect_raises(self):
        records = [
            {
                "injected_true_effect": 0.5,
                "ci_lower": 0.3,
                "ci_upper": 0.7,
            }
        ]
        with pytest.raises(KeyError):
            compute_metrics_from_simulation(records)

class TestComputeMetrics:
    def test_multiple_records(self):
        records = [
            {
                "replicate_id": i,
                "injected_true_effect": 0.5,
                "pooled_effect": p,
                "ci_lower": c - 0.2,
                "ci_upper": c + 0.2,
            }
            for i, (p, c) in enumerate(
                [(0.5, 0.5), (0.6, 0.6), (0.9, 0.7)]
            )
        ]
        results = compute_metrics_from_simulation(records)
        assert len(results) == 3
        assert results[0].bias == 0.0
        assert results[0].coverage_flag is True
        assert results[1].bias == pytest.approx(0.1)
        assert results[1].coverage_flag is True
        assert results[2].bias == pytest.approx(0.4)
        assert results[2].coverage_flag is False  # 0.5 not in [0.5, 0.9]... see below

    def test_empty_input(self):
        assert compute_metrics_from_simulation([]) == []

    def test_i_squared_computed_from_effect_sizes(self):
        records = [
            {
                "injected_true_effect": 0.0,
                "pooled_effect": 0.0,
                "ci_lower": -0.5,
                "ci_upper": 0.5,
                "effect_sizes": [1.0, -1.0, 1.0, -1.0],
                "standard_errors": [1.0, 1.0, 1.0, 1.0],
            }
        ]
        r = compute_metrics_from_simulation(records)[0]
        # Q = 4, df = 3 -> I^2 = 25%
        assert r.i_squared == pytest.approx(25.0)

class TestAggregateMetrics:
    def test_aggregate_basic(self):
        results = [
            MetricsResult(0, 0.5, 0.5, 0.3, 0.7, 0.0, 0.0, 0.0, True),
            MetricsResult(1, 0.5, 0.6, 0.4, 0.8, 0.1, 10.0, 0.1, True),
            MetricsResult(2, 0.5, 0.9, 0.7, 1.1, 0.2, 50.0, 0.4, False),
        ]
        agg = aggregate_metrics(results)
        assert agg["total_replicates"] == 3
        assert agg["mean_bias"] == pytest.approx(0.5 / 3)
        assert agg["coverage_rate"] == pytest.approx(2.0 / 3.0)
        assert agg["mean_i_squared"] == pytest.approx(60.0 / 3.0)

    def test_aggregate_empty(self):
        agg = aggregate_metrics([])
        assert agg["total_replicates"] == 0
        assert agg["coverage_rate"] == 0.0

class TestISquared:
    def test_homogeneous_data_zero_i_squared(self):
        # All effect sizes equal -> Q = 0 -> I^2 = 0
        assert calculate_i_squared(
            [0.5, 0.5, 0.5], [0.1, 0.1, 0.1], 0.5
        ) == 0.0

    def test_single_study_returns_zero(self):
        assert calculate_i_squared([0.5], [0.1], 0.5) == 0.0

    def test_known_value(self):
        # Q = sum((y_i)^2) with y = +/-1, se = 1 -> Q = 4, df = 3
        val = calculate_i_squared(
            [1.0, -1.0, 1.0, -1.0], [1.0, 1.0, 1.0, 1.0], 0.0
        )
        assert val == pytest.approx(25.0)