"""
Unit tests for the metrics calculation module.

These tests verify that:
  * When the pooled estimate exactly equals the true effect,
    bias is zero and the coverage flag is True.
  * Aggregation of multiple MetricsResult objects produces the
    correct mean bias and coverage rate.
"""
import pytest

from analysis.metrics import (
    compute_metrics_from_simulation,
    aggregate_metrics,
    MetricsResult,
)


def test_compute_metrics_zero_bias_and_coverage():
    """
    A record where the pooled estimate equals the true effect should
    yield zero bias and a coverage flag of True.
    """
    record = {
        "injected_true_effect": 0.5,
        "pooled_effect": 0.5,
        "ci_lower": 0.0,
        "ci_upper": 1.0,
        "replicate_id": 1,
        "effect_sizes": [0.4, 0.6],
        "standard_errors": [0.1, 0.1],
    }

    results = compute_metrics_from_simulation([record])
    assert len(results) == 1

    mr = results[0]
    assert mr.bias == pytest.approx(0.0)
    assert mr.coverage_flag is True


def test_aggregate_metrics():
    """
    Aggregating two MetricsResult objects should produce the correct
    mean bias and coverage rate.
    """
    mr1 = MetricsResult(
        replicate_id=1,
        true_effect=0.5,
        pooled_estimate=0.5,
        ci_lower=0.0,
        ci_upper=1.0,
        tau_squared_estimate=0.0,
        i_squared=0.0,
        bias=0.0,
        coverage_flag=True,
    )
    mr2 = MetricsResult(
        replicate_id=2,
        true_effect=0.5,
        pooled_estimate=0.7,
        ci_lower=0.0,
        ci_upper=1.0,
        tau_squared_estimate=0.0,
        i_squared=0.0,
        bias=0.2,
        coverage_flag=False,
    )

    agg = aggregate_metrics([mr1, mr2])
    assert agg["mean_bias"] == pytest.approx(0.1)
    assert agg["coverage_rate"] == pytest.approx(0.5)
