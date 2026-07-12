"""
Unit tests for the outcome type detector.
"""

import pytest
from code.src.audit.test_type_detector import (
    detect_outcome_type,
    detect_outcome_types_batch,
    validate_outcome_type_consistency,
    OUTCOME_BINARY,
    OUTCOME_CONTINUOUS,
    OUTCOME_UNKNOWN
)
from code.src.models.data_models import ABTestSummary


class TestOutcomeTypeDetector:
    """Tests for outcome type detection heuristics."""

    def test_detect_binary_from_conversion_rates(self):
        """Test detection of binary outcome from conversion rates."""
        summary = ABTestSummary(
            source_url="http://example.com/test1",
            test_name="Conversion Test",
            baseline_conversion_rate=0.15,
            treatment_conversion_rate=0.18,
            baseline_sample_size=1000,
            treatment_sample_size=1000,
            p_value=0.03
        )
        outcome_type = detect_outcome_type(summary)
        assert outcome_type == OUTCOME_BINARY

    def test_detect_continuous_from_means(self):
        """Test detection of continuous outcome from mean values."""
        summary = ABTestSummary(
            source_url="http://example.com/test2",
            test_name="Duration Test",
            baseline_mean=120.5,
            treatment_mean=135.2,
            baseline_std=45.0,
            treatment_std=48.0,
            baseline_sample_size=500,
            treatment_sample_size=500,
            p_value=0.01
        )
        outcome_type = detect_outcome_type(summary)
        assert outcome_type == OUTCOME_CONTINUOUS

    def test_detect_continuous_from_std_devs(self):
        """Test detection of continuous outcome from standard deviation values."""
        summary = ABTestSummary(
            source_url="http://example.com/test3",
            test_name="Revenue Test",
            baseline_mean=None,
            treatment_mean=None,
            baseline_std=10.5,
            treatment_std=12.0,
            baseline_sample_size=300,
            treatment_sample_size=300,
            p_value=0.04
        )
        outcome_type = detect_outcome_type(summary)
        assert outcome_type == OUTCOME_CONTINUOUS

    def test_detect_binary_from_event_counts(self):
        """Test detection of binary outcome from event counts."""
        summary = ABTestSummary(
            source_url="http://example.com/test4",
            test_name="Click Test",
            n_events_baseline=150,
            n_events_treatment=180,
            baseline_sample_size=1000,
            treatment_sample_size=1000,
            p_value=0.02
        )
        outcome_type = detect_outcome_type(summary)
        assert outcome_type == OUTCOME_BINARY

    def test_detect_binary_from_test_name_keywords(self):
        """Test detection of binary outcome from test name keywords."""
        summary = ABTestSummary(
            source_url="http://example.com/test5",
            test_name="Conversion Rate Improvement Test",
            baseline_sample_size=500,
            treatment_sample_size=500,
            p_value=0.05
        )
        outcome_type = detect_outcome_type(summary)
        assert outcome_type == OUTCOME_BINARY

    def test_detect_continuous_from_test_name_keywords(self):
        """Test detection of continuous outcome from test name keywords."""
        summary = ABTestSummary(
            source_url="http://example.com/test6",
            test_name="Average Time on Site Test",
            baseline_sample_size=500,
            treatment_sample_size=500,
            p_value=0.05
        )
        outcome_type = detect_outcome_type(summary)
        assert outcome_type == OUTCOME_CONTINUOUS

    def test_detect_unknown_outcome(self):
        """Test detection of unknown outcome when no indicators are present."""
        summary = ABTestSummary(
            source_url="http://example.com/test7",
            test_name="Generic Test",
            baseline_sample_size=200,
            treatment_sample_size=200,
            p_value=0.05
        )
        outcome_type = detect_outcome_type(summary)
        assert outcome_type == OUTCOME_UNKNOWN

    def test_detect_unknown_from_none_summary(self):
        """Test detection returns unknown for None summary."""
        outcome_type = detect_outcome_type(None)
        assert outcome_type == OUTCOME_UNKNOWN

    def test_batch_detection(self):
        """Test batch detection of outcome types."""
        summaries = [
            ABTestSummary(
                source_url="http://example.com/binary1",
                test_name="Conversion Test",
                baseline_conversion_rate=0.15,
                treatment_conversion_rate=0.18,
                baseline_sample_size=1000,
                treatment_sample_size=1000,
                p_value=0.03
            ),
            ABTestSummary(
                source_url="http://example.com/continuous1",
                test_name="Duration Test",
                baseline_mean=120.5,
                treatment_mean=135.2,
                baseline_sample_size=500,
                treatment_sample_size=500,
                p_value=0.01
            )
        ]
        
        results = detect_outcome_types_batch(summaries)
        
        assert results["http://example.com/binary1"] == OUTCOME_BINARY
        assert results["http://example.com/continuous1"] == OUTCOME_CONTINUOUS

    def test_validate_consistency(self):
        """Test consistency validation returns correct counts."""
        summaries = [
            ABTestSummary(
                source_url="http://example.com/binary1",
                test_name="Conversion Test",
                baseline_conversion_rate=0.15,
                treatment_conversion_rate=0.18,
                baseline_sample_size=1000,
                treatment_sample_size=1000,
                p_value=0.03
            ),
            ABTestSummary(
                source_url="http://example.com/continuous1",
                test_name="Duration Test",
                baseline_mean=120.5,
                treatment_mean=135.2,
                baseline_sample_size=500,
                treatment_sample_size=500,
                p_value=0.01
            ),
            ABTestSummary(
                source_url="http://example.com/unknown1",
                test_name="Generic Test",
                baseline_sample_size=200,
                treatment_sample_size=200,
                p_value=0.05
            )
        ]
        
        binary, continuous, unknown = validate_outcome_type_consistency(summaries)
        
        assert binary == 1
        assert continuous == 1
        assert unknown == 1

    def test_priority_conversion_rates_over_event_counts(self):
        """Test that conversion rates take priority over event counts."""
        summary = ABTestSummary(
            source_url="http://example.com/priority1",
            test_name="Mixed Test",
            baseline_conversion_rate=0.15,
            treatment_conversion_rate=0.18,
            n_events_baseline=150,
            n_events_treatment=180,
            baseline_sample_size=1000,
            treatment_sample_size=1000,
            p_value=0.03
        )
        outcome_type = detect_outcome_type(summary)
        assert outcome_type == OUTCOME_BINARY

    def test_priority_means_over_event_counts(self):
        """Test that means take priority over event counts."""
        summary = ABTestSummary(
            source_url="http://example.com/priority2",
            test_name="Mixed Test",
            baseline_mean=120.5,
            treatment_mean=135.2,
            n_events_baseline=150,
            n_events_treatment=180,
            baseline_sample_size=1000,
            treatment_sample_size=1000,
            p_value=0.03
        )
        outcome_type = detect_outcome_type(summary)
        assert outcome_type == OUTCOME_CONTINUOUS
