"""Unit tests for the T022 trend direction logic (FR-005)."""
import pytest

from trend_direction import (
    MONOTONIC_DECREASE,
    MONOTONIC_INCREASE,
    NO_TREND,
    determine_trend_direction,
    trend_direction_from_metrics,
)


class TestDetermineTrendDirection:
    def test_negative_tau_reports_monotonic_decrease(self):
        assert determine_trend_direction(-0.6) == MONOTONIC_DECREASE

    def test_positive_tau_reports_monotonic_increase(self):
        assert determine_trend_direction(0.4) == MONOTONIC_INCREASE

    def test_zero_tau_reports_no_trend(self):
        assert determine_trend_direction(0.0) == NO_TREND

    def test_boundary_values(self):
        assert determine_trend_direction(-1.0) == MONOTONIC_DECREASE
        assert determine_trend_direction(1.0) == MONOTONIC_INCREASE

    def test_tiny_negative_is_decrease(self):
        assert determine_trend_direction(-1e-9) == MONOTONIC_DECREASE

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            determine_trend_direction(1.5)

    def test_nan_raises(self):
        with pytest.raises(ValueError):
            determine_trend_direction(float("nan"))

    def test_non_numeric_raises(self):
        with pytest.raises(TypeError):
            determine_trend_direction("negative")


class TestTrendDirectionFromMetrics:
    def test_declining_rho_sequence_reports_decrease(self):
        rows = [{"rho": str(v)} for v in (0.9, 0.7, 0.5, 0.3)]
        result = trend_direction_from_metrics(rows)
        assert result["trend_direction"] == MONOTONIC_DECREASE
        assert result["n_points"] == 4

    def test_increasing_sequence_reports_increase(self):
        rows = [{"rho": str(v)} for v in (0.1, 0.3, 0.6)]
        assert trend_direction_from_metrics(rows)["trend_direction"] == MONOTONIC_INCREASE

    def test_empty_rows_default_to_no_trend(self):
        result = trend_direction_from_metrics([])
        assert result["trend_direction"] == NO_TREND
        assert result["n_points"] == 0

    def test_prefers_tau_over_rho(self):
        rows = [{"tau": "-0.2", "rho": "0.9"}]
        result = trend_direction_from_metrics(rows)
        assert result["trend_direction"] == MONOTONIC_DECREASE

    def test_skips_non_numeric_values(self):
        rows = [{"rho": "abc"}, {"rho": "-0.5"}]
        result = trend_direction_from_metrics(rows)
        assert result["n_points"] == 1
        assert result["trend_direction"] == MONOTONIC_DECREASE