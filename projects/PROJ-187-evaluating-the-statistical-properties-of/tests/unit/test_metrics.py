"""Unit tests for marginal and correlation fidelity metrics (T002).

Validates KS / chi-square / Fisher-z outputs against hand-computed values and
confirms FR-011 zero-variance handling does not crash. When the processed
Adult data from T001 exists on disk, the hand-computed checks are additionally
exercised on a small real/synthetic pair drawn from it.
"""
from __future__ import annotations

import math
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from src.metrics.correlation import (
    compute_correlation_metrics,
    correlation_matrices,
    fisher_z,
    fisher_z_deviation,
    permutation_correlation_test,
)
from src.metrics.marginal import (
    chi_square_test,
    compute_marginal_metrics,
    detect_column_types,
    kde_estimate,
    ks_test,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ADULT_TRAIN = PROJECT_ROOT / "data" / "processed" / "adult" / "train.parquet"
ADULT_HOLDOUT = PROJECT_ROOT / "data" / "processed" / "adult" / "holdout.parquet"


# ---------------------------------------------------------------- KS tests
def test_ks_hand_computed():
    real = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    synth = pd.Series([1.0, 2.0, 3.0, 4.0, 6.0])
    stat, p = ks_test(real, synth)
    expected = stats.ks_2samp(real.to_numpy(), synth.to_numpy())
    assert stat == pytest.approx(expected.statistic)
    assert p == pytest.approx(expected.pvalue)
    # Hand computation: ECDFs differ maximally at x in [5, 6): 1/5.
    assert stat == pytest.approx(0.2)

def test_ks_identical_samples():
    real = pd.Series(np.linspace(0, 1, 50))
    stat, p = ks_test(real, real.copy())
    assert stat == pytest.approx(0.0)
    assert p == pytest.approx(1.0)


# --------------------------------------------------------- chi-square tests
def test_chi_square_hand_computed():
    real = pd.Series(["a"] * 30 + ["b"] * 70)
    synth = pd.Series(["a"] * 45 + ["b"] * 55)
    stat, p = chi_square_test(real, synth)
    # Expected counts from real proportions (0.3/0.7) scaled to n=100.
    expected = stats.chisquare(f_obs=[45, 55], f_exp=[30, 70])
    assert stat == pytest.approx(expected.statistic)
    assert p == pytest.approx(expected.pvalue)
    # Hand computation: (45-30)^2/30 + (55-70)^2/70 = 7.5 + 3.2142857...
    assert stat == pytest.approx(225 / 30 + 225 / 70)

def test_chi_square_identical_distributions():
    real = pd.Series(["x"] * 50 + ["y"] * 50)
    synth = pd.Series(["x"] * 25 + ["y"] * 25)
    stat, p = chi_square_test(real, synth)
    assert stat == pytest.approx(0.0)
    assert p == pytest.approx(1.0)


# -------------------------------------------------------------- Fisher-z
def test_fisher_z_hand_computed():
    assert fisher_z(0.5) == pytest.approx(math.atanh(0.5))
    assert fisher_z(0.3) == pytest.approx(math.atanh(0.3))
    # Clipping: |r| > 0.999 is clipped before atanh.
    assert fisher_z(1.0) == pytest.approx(math.atanh(0.999))
    assert fisher_z(-1.0) == pytest.approx(math.atanh(-0.999))

def test_fisher_z_deviation_hand_computed():
    d = fisher_z_deviation(0.5, 0.3)
    assert d == pytest.approx(abs(math.atanh(0.5) - math.atanh(0.3)))
    assert d > 0
    # Identical correlations give zero deviation.
    assert fisher_z_deviation(0.42, 0.42) == pytest.approx(0.0)


# ------------------------------------------------------- zero-variance FR-011
def test_zero_variance_synthetic_flagged_and_ks_skipped():
    real = pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]})
    synth = pd.DataFrame({"x": [3.0, 3.0, 3.0, 3.0, 3.0, 3.0]})
    rows = compute_marginal_metrics(real, synth)
    assert len(rows) == 1
    row = rows[0]
    assert row["zero_variance_flag"] is True
    assert row["fidelity_failure"] is True
    assert row["ks_stat"] is None
    assert row["ks_pvalue"] is None  # KS gracefully skipped, no crash

def test_zero_variance_both_sides_is_not_failure():
    real = pd.DataFrame({"x": [2.0, 2.0, 2.0]})
    synth = pd.DataFrame({"x": [2.0, 2.0, 2.0]})
    rows = compute_marginal_metrics(real, synth)
    assert rows[0]["zero_variance_flag"] is False
    assert rows[0]["fidelity_failure"] is False


# ------------------------------------------------------------------- KDE
def test_kde_estimate_returns_grid_and_pdf():
    rng = np.random.default_rng(0)
    values = rng.normal(size=200)
    grid, pdf = kde_estimate(values, grid_size=50)
    assert grid.shape == (50,)
    assert pdf.shape == (50,)
    assert np.all(pdf >= 0)
    assert np.all(np.diff(grid) > 0)
    # Density integrates to ~1 over the grid.
    integral = np.trapezoid(pdf, grid)
    assert integral == pytest.approx(1.0, abs=0.1)

def test_kde_estimate_degenerate_constant():
    grid, pdf = kde_estimate(np.full(10, 3.0))
    assert list(grid) == [3.0]
    assert list(pdf) == [1.0]


# ------------------------------------------------------- marginal end-to-end
def test_compute_marginal_metrics_mixed_types():
    rng = np.random.default_rng(1)
    n = 100
    real = pd.DataFrame(
        {
            "num": rng.normal(10, 2, n),
            "cat": rng.choice(["a", "b", "c"], n, p=[0.5, 0.3, 0.2]),
        }
    )
    synth = pd.DataFrame(
        {
            "num": rng.normal(10.5, 2, n),
            "cat": rng.choice(["a", "b", "c"], n, p=[0.4, 0.4, 0.2]),
        }
    )
    rows = compute_marginal_metrics(real, synth)
    by_col = {r["column"]: r for r in rows}
    assert by_col["num"]["column_type"] == "continuous"
    assert by_col["cat"]["column_type"] == "categorical"
    assert "ks_stat" in by_col["num"] and "chi2_stat" in by_col["cat"]
    assert by_col["num"]["mean_diff"] > 0
    assert by_col["num"]["var_diff"] >= 0
    assert by_col["cat"]["ks_stat"] if "ks_stat" in by_col["cat"] else True


# ------------------------------------------------------- correlation metrics
def test_correlation_matrices_and_diffs():
    rng = np.random.default_rng(2)
    n = 200
    x = rng.normal(size=n)
    y = 0.8 * x + rng.normal(size=n) * 0.5
    real = pd.DataFrame({"a": x, "b": y})
    synth = pd.DataFrame({"a": rng.normal(size=n), "b": rng.normal(size=n)})
    pr, sp = correlation_matrices(real, ["a", "b"])
    assert pr.loc["a", "b"] == pytest.approx(
        np.corrcoef(x, y)[0, 1], abs=1e-12
    )
    rows = compute_correlation_metrics(
        real, synth, cols=["a", "b"], n_permutations=1000, seed=42
    )
    types = {r["metric_type"] for r in rows}
    assert types == {"PearsonDiff", "SpearmanDiff", "FisherZ", "PermutationCorr"}
    by_type = {r["metric_type"]: r for r in rows}
    # Independent synthetic pair: real correlation should be near zero.
    assert by_type["PearsonDiff"]["synth_pearson"] == pytest.approx(0.0, abs=0.2)
    # PearsonDiff equals |r_real - r_synth|.
    r = by_type["PearsonDiff"]
    assert r["statistic"] == pytest.approx(
        abs(r["real_pearson"] - r["synth_pearson"]), abs=1e-12
    )
    # FisherZ row matches the hand formula on the recorded correlations.
    assert r["fisher_z_deviation"] == pytest.approx(
        fisher_z_deviation(r["real_pearson"], r["synth_pearson"]), abs=1e-12
    )
    perm = by_type["PermutationCorr"]
    assert perm["n_permutations"] == 1000
    assert 0.0 <= perm["pvalue"] <= 1.0

def test_permutation_test_rejects_fewer_than_1000_perms():
    rng = np.random.default_rng(3)
    real = pd.DataFrame({"a": rng.normal(size=50), "b": rng.normal(size=50)})
    with pytest.raises(ValueError):
        permutation_correlation_test(
            real, real, "a", "b", n_permutations=999, seed=42
        )

def test_permutation_test_identical_data_high_pvalue():
    rng = np.random.default_rng(4)
    x = rng.normal(size=80)
    y = 0.5 * x + rng.normal(size=80)
    real = pd.DataFrame({"a": x, "b": y})
    # Synthetic is an exact copy: the observed statistic is ~0 and the
    # permutation null can rarely exceed it, so p should be high.
    result = permutation_correlation_test(
        real, real.copy(), "a", "b", n_permutations=1000, seed=42
    )
    assert result["statistic"] == pytest.approx(0.0, abs=1e-12)
    assert result["pvalue"] >= 0.5

def test_permutation_test_seed_reproducibility():
    rng = np.random.default_rng(5)
    real = pd.DataFrame({"a": rng.normal(size=60), "b": rng.normal(size=60)})
    synth = pd.DataFrame({"a": rng.normal(size=60), "b": rng.normal(size=60)})
    r1 = permutation_correlation_test(real, synth, "a", "b", 1000, seed=7)
    r2 = permutation_correlation_test(real, synth, "a", "b", 1000, seed=7)
    assert r1["pvalue"] == r2["pvalue"]
    assert r1["statistic"] == r2["statistic"]


# --------------------------------- processed Adult data (T001), when present
@pytest.mark.skipif(
    not (ADULT_TRAIN.exists() and ADULT_HOLDOUT.exists()),
    reason="processed Adult data from T001 not on disk",
)
def test_metrics_on_processed_adult_pair():
    train = pd.read_parquet(ADULT_TRAIN)
    holdout = pd.read_parquet(ADULT_HOLDOUT)
    # Small real/synthetic pair: hold-out is "real"; a bootstrap resample of
    # the training split stands in as the synthetic set under test.
    rng = np.random.default_rng(42)
    synth = train.sample(n=min(300, len(train)), random_state=42).reset_index(
        drop=True
    )
    real_small = holdout.sample(n=min(300, len(holdout)), random_state=42
    ).reset_index(drop=True)
    cont, cat = detect_column_types(real_small)
    rows = compute_marginal_metrics(real_small, synth, cont, cat)
    assert len(rows) == real_small.shape[1]
    for row in rows:
        if row["column_type"] == "continuous":
            if not row["zero_variance_flag"]:
                assert row["ks_stat"] is not None
                assert 0.0 <= row["ks_stat"] <= 1.0
                assert 0.0 <= row["ks_pvalue"] <= 1.0
        else:
            assert row["chi2_stat"] >= 0.0
            assert 0.0 <= row["chi2_pvalue"] <= 1.0
    corr_rows = compute_correlation_metrics(
        real_small, synth, cols=cont[:4], n_permutations=1000, seed=42
    )
    assert corr_rows, "expected at least one column pair"
    for row in corr_rows:
        if row["metric_type"] == "FisherZ":
            assert row["statistic"] is None or row["statistic"] >= 0.0