"""
Unit tests for code/analysis/metrics.py (Task T004, FR-003).

Verification requirement: a pooled estimate exactly equal to the true
effect results in zero bias and a coverage flag of True.

Runnable both under pytest and standalone:
    python tests/unit/test_metrics.py
The standalone run writes an execution-evidence file to
data/results/metrics_verification.json.
"""
import json
import math
import os
import sys
from pathlib import Path

# Make the code/ package importable regardless of invocation directory.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from analysis.metrics import (  # noqa: E402
    MetricsResult,
    calculate_bias,
    calculate_coverage,
    calculate_i_squared,
    compute_metrics_from_simulation,
    aggregate_metrics,
    _extract_true_effect,
    TRUE_EFFECT_COLUMN,
)


def test_zero_bias_when_pooled_equals_true_effect():
    """Pooled estimate exactly equal to the true effect -> zero bias."""
    assert calculate_bias(0.5, 0.5) == 0.0
    assert calculate_bias(-1.25, -1.25) == 0.0
    assert calculate_bias(0.0, 0.0) == 0.0


def test_bias_sign_and_magnitude():
    assert math.isclose(calculate_bias(0.7, 0.5), 0.2)
    assert math.isclose(calculate_bias(0.3, 0.5), -0.2)


def test_coverage_true_when_true_effect_inside_ci():
    """Pooled == true effect with a CI around it -> coverage flag True."""
    assert calculate_coverage(0.4, 0.6, 0.5) is True
    # Inclusive bounds
    assert calculate_coverage(0.5, 0.6, 0.5) is True
    assert calculate_coverage(0.4, 0.5, 0.5) is True


def test_coverage_false_when_true_effect_outside_ci():
    assert calculate_coverage(0.6, 0.8, 0.5) is False
    assert calculate_coverage(-0.2, 0.1, 0.5) is False


def test_extract_true_effect_strict_column():
    record = {"injected_true_effect": 0.5, "pooled_effect": 0.4}
    assert _extract_true_effect(record) == 0.5
    # String numerics are coerced
    assert _extract_true_effect({"injected_true_effect": "0.25"}) == 0.25


def test_extract_true_effect_missing_column_raises():
    """No fallback column may ever be consulted (FR-003)."""
    try:
        _extract_true_effect({"true_effect": 0.5, "pooled_effect": 0.4})
    except KeyError as e:
        assert TRUE_EFFECT_COLUMN in str(e)
    else:
        raise AssertionError("KeyError expected for missing injected_true_effect")


def test_extract_true_effect_non_finite_raises():
    for bad in (float("nan"), float("inf"), "not_a_number", None):
        try:
            _extract_true_effect({"injected_true_effect": bad})
        except ValueError:
            pass
        else:
            raise AssertionError(f"ValueError expected for {bad!r}")


def test_compute_metrics_zero_bias_and_coverage_true():
    """End-to-end: pooled == true effect -> bias 0, coverage True."""
    records = [
        {
            "replicate_id": 0,
            "injected_true_effect": 0.5,
            "pooled_effect": 0.5,
            "ci_lower": 0.4,
            "ci_upper": 0.6,
        },
        {
            "replicate_id": 1,
            "injected_true_effect": 0.5,
            "pooled_effect": 0.5,
            "ci_lower": 0.45,
            "ci_upper": 0.55,
        },
    ]
    results = compute_metrics_from_simulation(records)
    assert len(results) == 2
    for r in results:
        assert r.bias == 0.0
        assert r.coverage_flag is True
        assert r.true_effect == 0.5


def test_compute_metrics_missing_true_effect_column_raises():
    try:
        compute_metrics_from_simulation(
            [{"pooled_effect": 0.5, "ci_lower": 0.4, "ci_upper": 0.6}]
        )
    except KeyError:
        pass
    else:
        raise AssertionError("KeyError expected when injected_true_effect absent")


def test_compute_metrics_missing_pooled_column_raises():
    try:
        compute_metrics_from_simulation(
            [{"injected_true_effect": 0.5, "ci_lower": 0.4, "ci_upper": 0.6}]
        )
    except KeyError:
        pass
    else:
        raise AssertionError("KeyError expected when pooled_effect absent")


def test_compute_metrics_empty_input():
    assert compute_metrics_from_simulation([]) == []


def test_compute_metrics_i_squared_fallback():
    """i_squared computed from effect sizes / SEs when not provided."""
    records = [
        {
            "replicate_id": 0,
            "injected_true_effect": 0.0,
            "pooled_effect": 0.0,
            "ci_lower": -1.0,
            "ci_upper": 1.0,
            "effect_sizes": [1.0, -1.0, 1.0, -1.0],
            "standard_errors": [0.5, 0.5, 0.5, 0.5],
        }
    ]
    results = compute_metrics_from_simulation(records)
    assert results[0].i_squared > 0.0


def test_aggregate_metrics():
    results = [
        MetricsResult(0, 0.5, 0.5, 0.4, 0.6, 0.0, 0.0, 0.0, True),
        MetricsResult(1, 0.5, 0.6, 0.5, 0.7, 0.0, 0.0, 0.1, True),
        MetricsResult(2, 0.5, 0.2, 0.15, 0.25, 0.0, 0.0, -0.3, False),
    ]
    agg = aggregate_metrics(results)
    assert math.isclose(agg["mean_bias"], (0.0 + 0.1 - 0.3) / 3.0)
    assert math.isclose(agg["coverage_rate"], 2.0 / 3.0)
    assert agg["total_replicates"] == 3


def test_aggregate_metrics_empty():
    agg = aggregate_metrics([])
    assert agg["total_replicates"] == 0
    assert agg["coverage_rate"] == 0.0


def test_calculate_i_squared_zero_for_homogeneous():
    """Homogeneous effects -> Q ~ df -> I^2 clamped to 0."""
    i2 = calculate_i_squared([0.5, 0.5, 0.5], [0.1, 0.1, 0.1], 0.5)
    assert i2 == 0.0


def test_calculate_i_squared_positive_for_heterogeneous():
    i2 = calculate_i_squared([1.0, -1.0, 1.0, -1.0], [0.5] * 4, 0.0)
    assert i2 > 0.0
    assert i2 <= 100.0


def _run_all():
    tests = [(k, v) for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    outcomes = {}
    n_failed = 0
    for name, fn in tests:
        try:
            fn()
            outcomes[name] = "passed"
        except Exception as e:  # noqa: BLE001
            outcomes[name] = f"failed: {type(e).__name__}: {e}"
            n_failed += 1
    return tests, outcomes, n_failed


def main():
    tests, outcomes, n_failed = _run_all()
    report = {
        "task_id": "T004",
        "test_file": "tests/unit/test_metrics.py",
        "n_tests": len(tests),
        "n_passed": len(tests) - n_failed,
        "all_passed": n_failed == 0,
        "tests": outcomes,
    }
    out_dir = PROJECT_ROOT / "data" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "metrics_verification.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    for name, status in outcomes.items():
        print(f"{name}: {status}")
    print(f"\n{n_failed == 0 and 'ALL PASSED' or 'FAILURES'}: "
          f"{report['n_passed']}/{len(tests)} tests passed.")
    print(f"Evidence written to {out_path}")
    return 0 if n_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())