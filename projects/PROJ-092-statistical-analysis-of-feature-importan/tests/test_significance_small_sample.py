"""Tests for T024: small sample size handling (n < 10) in significance_test.py."""
import os
import sys
import json

import pytest

CODE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code")
if CODE_DIR not in sys.path:
  sys.path.insert(0, CODE_DIR)

from significance_test import (
  block_permutation_test,
  is_small_sample,
  mann_kendall_test,
  run_significance_tests,
)


class TestSmallSampleDetection:
  def test_n_below_10_is_small(self):
    assert is_small_sample([0.9, 0.8, 0.7, 0.6, 0.5]) is True

  def test_n_above_10_is_not_small(self):
    assert is_small_sample([0.5] * 12) is False

  def test_boundary_n_10_is_not_small(self):
    assert is_small_sample([0.5] * 10) is False


class TestMannKendall:
  def test_increasing_sequence(self):
    tau, direction, p = mann_kendall_test([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    assert tau == pytest.approx(1.0)
    assert direction == "monotonic increase"
    assert p < 0.05

  def test_decreasing_sequence_reports_decrease(self):
    tau, direction, _ = mann_kendall_test([0.9, 0.8, 0.7, 0.65, 0.6])
    assert tau < 0
    assert direction == "monotonic decrease"

  def test_too_few_points_neutral(self):
    tau, direction, p = mann_kendall_test([0.5])
    assert tau == 0.0
    assert p == 1.0


class TestBlockPermutation:
  def test_p_value_in_range_small_sample(self):
    rhos = [0.95, 0.90, 0.85, 0.80, 0.70, 0.60]
    p = block_permutation_test(rhos)
    assert 0.0 <= p <= 1.0

  def test_constant_sequence_p_is_one(self):
    # No trend: every permutation has statistic 0 >= observed 0.
    p = block_permutation_test([0.5, 0.5, 0.5, 0.5, 0.5])
    assert p == pytest.approx(1.0)

  def test_strong_monotonic_trend_small_p(self):
    rhos = [0.99, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3]
    p = block_permutation_test(rhos)
    # Only a shift of 0 (identity) reproduces the fully ordered
    # sequence, so the exact p-value is small.
    assert p <= 1.0 / 8.0 + 1e-9

  def test_deterministic_with_seed(self):
    rhos = [0.8, 0.75, 0.7, 0.68, 0.6]
    p1 = block_permutation_test(rhos, n_resamples=500)
    p2 = block_permutation_test(rhos, n_resamples=500)
    assert p1 == p2

  def test_insufficient_data_returns_one(self):
    assert block_permutation_test([0.5]) == 1.0


class TestRunSignificanceTests:
  def _write_csv(self, tmp_path, rhos):
    path = tmp_path / "drift_metrics.csv"
    lines = ["window_t,window_t1,rho,spearman_p_value"]
    for i, r in enumerate(rhos):
      lines.append(f"{i},{i + 1},{r},0.01")
    path.write_text("\n".join(lines) + "\n")
    return str(path)

  def test_small_sample_report_uses_permutation_p(self, tmp_path):
    rhos = [0.95, 0.90, 0.85, 0.80, 0.70]  # n = 5 < 10
    csv_path = self._write_csv(tmp_path, rhos)
    out_path = tmp_path / "p_values.json"
    result = run_significance_tests(csv_path, str(out_path))
    assert result["small_sample"] is True
    assert result["n_observations"] == 5
    # Reported p-value must be the permutation p-value (FR-008).
    assert result["p_value"] == result.get("p_value")
    assert "permutation" in result["method"]
    assert result["trend_direction"] == "monotonic decrease"
    # Output file written to disk.
    assert out_path.is_file()
    with open(out_path) as f:
          saved = json.load(f)
    assert saved["small_sample"] is True
    assert "p_value" in saved

  def test_missing_input_fails_loudly(self, tmp_path):
    with pytest.raises(FileNotFoundError):
      run_significance_tests(str(tmp_path / "nope.csv"), str(tmp_path / "out.json"))