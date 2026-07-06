"""
Unit tests for drift_metric schema and calculations.
"""
import pytest
from contracts.drift_metric import RankCorrelationMetric, TrendMetric, GlobalStats

def test_rank_correlation_magnitude_classification():
    """Test magnitude classification based on rho deviation."""
    # No drift
    metric1 = RankCorrelationMetric(window_t=1, window_t_plus_1=2, rho=0.95, p_value=0.01)
    assert metric1.magnitude == "none"

    # Low drift
    metric2 = RankCorrelationMetric(window_t=1, window_t_plus_1=2, rho=0.85, p_value=0.01)
    assert metric2.magnitude == "low"

    # Medium drift
    metric3 = RankCorrelationMetric(window_t=1, window_t_plus_1=2, rho=0.70, p_value=0.01)
    assert metric3.magnitude == "medium"

    # High drift
    metric4 = RankCorrelationMetric(window_t=1, window_t_plus_1=2, rho=0.40, p_value=0.01)
    assert metric4.magnitude == "high"

def test_rank_correlation_significance():
    """Test significance flagging."""
    metric1 = RankCorrelationMetric(window_t=1, window_t_plus_1=2, rho=0.5, p_value=0.04)
    assert metric1.significant_at_005 is True

    metric2 = RankCorrelationMetric(window_t=1, window_t_plus_1=2, rho=0.5, p_value=0.06)
    assert metric2.significant_at_005 is False

def test_trend_metric_direction():
    """Test trend direction classification."""
    # Increasing trend
    trend1 = TrendMetric(
        sequence_type="rho",
        kendall_tau=0.5,
        p_value=0.01,
        sample_size=10
    )
    assert trend1.trend_direction == "increasing"

    # Decreasing trend
    trend2 = TrendMetric(
        sequence_type="rho",
        kendall_tau=-0.5,
        p_value=0.01,
        sample_size=10
    )
    assert trend2.trend_direction == "decreasing"

    # No trend
    trend3 = TrendMetric(
        sequence_type="rho",
        kendall_tau=0.05,
        p_value=0.01,
        sample_size=10
    )
    assert trend3.trend_direction == "no_trend"
