"""
Unit tests for outcome-type detection heuristics.
"""

import pytest
from code.src.models.data_models import ABTestSummary
from code.src.audit.test_type_detector import detect_outcome_type, detect_outcome_types_batch


class TestBinaryOutcomeDetection:
    """Tests for detecting binary outcomes."""

    def test_conversion_rate_fields(self):
        """Should detect binary when conversion rate fields are present."""
        summary = ABTestSummary(
            url="https://example.com/test1",
            baseline_conversion_rate=0.05,
            treatment_conversion_rate=0.06,
            sample_size=10000
        )
        assert detect_outcome_type(summary) == "binary"

    def test_conversion_rate_keywords_in_metric_name(self):
        """Should detect binary when metric name contains conversion keywords."""
        summary = ABTestSummary(
            url="https://example.com/test2",
            metric_name="Conversion Rate",
            sample_size=5000
        )
        assert detect_outcome_type(summary) == "binary"

    def test_proportion_range_with_rate_keyword(self):
        """Should detect binary when values are in 0-1 range and have rate keyword."""
        summary = ABTestSummary(
            url="https://example.com/test3",
            baseline_rate=0.12,
            treatment_rate=0.15,
            sample_size=2000
        )
        assert detect_outcome_type(summary) == "binary"


class TestContinuousOutcomeDetection:
    """Tests for detecting continuous outcomes."""

    def test_mean_std_fields(self):
        """Should detect continuous when mean and std fields are present."""
        summary = ABTestSummary(
            url="https://example.com/test4",
            baseline_mean=50.5,
            treatment_mean=55.2,
            baseline_std=10.0,
            treatment_std=12.0,
            sample_size=1000
        )
        assert detect_outcome_type(summary) == "continuous"

    def test_mean_only_with_continuous_keyword(self):
        """Should detect continuous when mean is present with continuous keywords."""
        summary = ABTestSummary(
            url="https://example.com/test5",
            metric_name="Average Order Value",
            baseline_mean=45.0,
            treatment_mean=48.0
        )
        assert detect_outcome_type(summary) == "continuous"

    def test_duration_metric(self):
        """Should detect continuous for time/duration metrics."""
        summary = ABTestSummary(
            url="https://example.com/test6",
            metric_name="Time on Site",
            baseline_mean=120.0,
            treatment_mean=135.0
        )
        assert detect_outcome_type(summary) == "continuous"


class TestUnknownOutcomeDetection:
    """Tests for cases where outcome type cannot be determined."""

    def test_missing_key_fields(self):
        """Should return unknown when insufficient fields are present."""
        summary = ABTestSummary(
            url="https://example.com/test7",
            sample_size=100
        )
        assert detect_outcome_type(summary) == "unknown"

    def test_arbitrary_metric_no_keywords(self):
        """Should return unknown for arbitrary metrics without keywords."""
        summary = ABTestSummary(
            url="https://example.com/test8",
            metric_name="Some Random Metric",
            value=100
        )
        assert detect_outcome_type(summary) == "unknown"


class TestBatchDetection:
    """Tests for batch detection functionality."""

    def test_batch_processing(self):
        """Should process multiple summaries correctly."""
        summaries = [
            ABTestSummary(url="https://example.com/b1", baseline_conversion_rate=0.05),
            ABTestSummary(url="https://example.com/c1", baseline_mean=50.0, baseline_std=10.0),
            ABTestSummary(url="https://example.com/u1", sample_size=100)
        ]
        
        results = detect_outcome_types_batch(summaries)
        
        assert len(results) == 3
        assert results[0]["outcome_type"] == "binary"
        assert results[1]["outcome_type"] == "continuous"
        assert results[2]["outcome_type"] == "unknown"

    def test_batch_url_preservation(self):
        """Should preserve URLs in batch results."""
        urls = ["https://a.com", "https://b.com", "https://c.com"]
        summaries = [
            ABTestSummary(url=u, baseline_conversion_rate=0.05) for u in urls
        ]
        
        results = detect_outcome_types_batch(summaries)
        
        for i, result in enumerate(results):
            assert result["url"] == urls[i]
            assert result["outcome_type"] == "binary"
            assert result["detection_status"] == "success"
