"""Unit tests for the pairwise drift calculation logic (T017, FR-004)."""
import os
import sys

import pytest

# Make code/ importable regardless of the working directory
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "code"
    ),
)

from drift_analysis import (
    calculate_rank_correlation,
    compute_pairwise_drift,
    extract_window_rankings,
    flag_high_drift,
    save_drift_metrics,
)


class TestCalculateRankCorrelation:
    def test_identical_rankings(self):
        a = ["f1", "f2", "f3", "f4"]
        rho, p = calculate_rank_correlation(a, list(a))
        assert rho == pytest.approx(1.0)
        assert p < 0.05

    def test_reversed_rankings(self):
        a = ["f1", "f2", "f3", "f4"]
        b = ["f4", "f3", "f2", "f1"]
        rho, _ = calculate_rank_correlation(a, b)
        assert rho == pytest.approx(-1.0)

    def test_mismatched_features_raise(self):
        with pytest.raises(ValueError):
            calculate_rank_correlation(["f1", "f2"], ["f1", "f3"])

    def test_too_few_features_raise(self):
        with pytest.raises(ValueError):
            calculate_rank_correlation(["f1"], ["f1"])


class TestComputePairwiseDrift:
    def _rankings(self):
        return {
            0: ["a", "b", "c", "d"],
            1: ["a", "b", "c", "d"],
            2: ["d", "c", "b", "a"],
            3: ["b", "a", "d", "c"],
        }

    def test_all_consecutive_pairs_computed(self):
        metrics = compute_pairwise_drift(self._rankings(), {}, {})
        assert len(metrics) == 3
        pairs = [(m["window_t"], m["window_t1"]) for m in metrics]
        assert pairs == [(0, 1), (1, 2), (2, 3)]

    def test_rho_values(self):
        metrics = compute_pairwise_drift(self._rankings(), {}, {})
        assert metrics[0]["rho"] == pytest.approx(1.0)
        assert metrics[1]["rho"] == pytest.approx(-1.0)
        assert -1.0 <= metrics[2]["rho"] <= 1.0

    def test_block_p_value_preferred(self):
        p_values = {0: 0.5}
        metrics = compute_pairwise_drift(self._rankings(), p_values, {})
        assert metrics[0]["block_permutation_p"] == 0.5
        assert metrics[0]["significant"] is False

    def test_null_baseline_mean_used(self):
        metrics = compute_pairwise_drift(
            self._rankings(), {}, {"mean": 0.25}
        )
        assert metrics[0]["null_mean_rho"] == pytest.approx(0.25)

    def test_empty_rankings_raise(self):
        with pytest.raises(ValueError):
            compute_pairwise_drift({}, {}, {})

    def test_single_window_yields_no_pairs(self):
        metrics = compute_pairwise_drift({0: ["a", "b"]}, {}, {})
        assert metrics == []

    def test_disjoint_feature_sets_skipped(self):
        rankings = {
            0: ["a", "b", "c"],
            1: ["x", "y", "z"],
            2: ["a", "b", "c"],
        }
        metrics = compute_pairwise_drift(rankings, {}, {})
        # Pair 0-1 has no common features; pair 1-2 neither
        assert metrics == []

    def test_common_subset_features(self):
        rankings = {
            0: ["a", "b", "c", "d"],
            1: ["b", "a", "c"],  # 'd' dropped in window 1
        }
        metrics = compute_pairwise_drift(rankings, {}, {})
        assert len(metrics) == 1
        assert metrics[0]["rho"] == pytest.approx(1.0)


class TestFlagHighDrift:
    def test_flagging(self):
        metrics = [
            {"spearman_p_value": 0.01, "block_permutation_p": 0.01},
            {"spearman_p_value": 0.01, "block_permutation_p": 0.9},
        ]
        flagged = flag_high_drift(metrics, {})
        assert flagged[0]["significant"] is True
        assert flagged[1]["significant"] is False


class TestExtractRankingsAndSave:
    def test_extract_orders_by_importance_desc(self):
        profiles = [
            {"window_id": 1, "feature_name": "x", "importance_score": 0.1},
            {"window_id": 1, "feature_name": "y", "importance_score": 0.5},
            {"window_id": 2, "feature_name": "y", "importance_score": 0.2},
            {"window_id": 2, "feature_name": "x", "importance_score": 0.3},
        ]
        rankings = extract_window_rankings(profiles)
        assert rankings[1] == ["y", "x"]
        assert rankings[2] == ["x", "y"]

    def test_save_drift_metrics_writes_csv(self, tmp_path):
        metrics = [
            {
                "window_t": 0,
                "window_t1": 1,
                "rho": 0.9,
                "spearman_p_value": 0.05,
                "block_permutation_p": 0.04,
                "null_mean_rho": 0.2,
                "significant": True,
            }
        ]
        out = tmp_path / "drift_metrics.csv"
        save_drift_metrics(metrics, str(out))
        content = out.read_text()
        assert "window_t,window_t1,rho" in content
        assert "0,1,0.9" in content