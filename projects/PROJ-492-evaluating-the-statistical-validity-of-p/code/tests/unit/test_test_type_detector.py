"""
Unit tests for the outcome-type detection heuristics (T022).
"""

import pytest
from code.src.models.data_models import ABTestSummary
from code.src.audit.test_type_detector import (
    detect_outcome_type,
    detect_outcome_types_for_batch,
    OUTCOME_TYPE_BINARY,
    OUTCOME_TYPE_CONTINUOUS,
    OUTCOME_TYPE_UNKNOWN,
)


def test_detect_binary_from_conversions():
    """Test that presence of conversions fields triggers binary detection."""
    summary = ABTestSummary(
        source_url="http://example.com/test1",
        conversions_control=100,
        conversions_treatment=120,
        sample_size_control=1000,
        sample_size_treatment=1000,
        p_value=0.03,
    )
    assert detect_outcome_type(summary) == OUTCOME_TYPE_BINARY


def test_detect_continuous_from_means():
    """Test that presence of mean fields triggers continuous detection."""
    summary = ABTestSummary(
        source_url="http://example.com/test2",
        mean_control=5.5,
        mean_treatment=6.2,
        std_control=1.0,
        std_treatment=1.2,
        sample_size_control=50,
        sample_size_treatment=50,
        p_value=0.01,
    )
    assert detect_outcome_type(summary) == OUTCOME_TYPE_CONTINUOUS


def test_binary_takes_precedence_over_continuous():
    """Test that if both are present, binary is chosen."""
    summary = ABTestSummary(
        source_url="http://example.com/test3",
        conversions_control=100,
        conversions_treatment=120,
        mean_control=5.5,
        mean_treatment=6.2,
        sample_size_control=1000,
        sample_size_treatment=1000,
        p_value=0.03,
    )
    assert detect_outcome_type(summary) == OUTCOME_TYPE_BINARY


def test_unknown_when_neither_present():
    """Test that unknown is returned if neither conversions nor means are present."""
    summary = ABTestSummary(
        source_url="http://example.com/test4",
        sample_size_control=100,
        sample_size_treatment=100,
        p_value=0.05,
    )
    assert detect_outcome_type(summary) == OUTCOME_TYPE_UNKNOWN


def test_batch_detection():
    """Test batch detection returns correct list of tuples."""
    summaries = [
        ABTestSummary(
            source_url="http://a.com",
            conversions_control=10,
            conversions_treatment=20,
            sample_size_control=100,
            sample_size_treatment=100,
            p_value=0.1,
        ),
        ABTestSummary(
            source_url="http://b.com",
            mean_control=1.0,
            mean_treatment=2.0,
            std_control=0.5,
            std_treatment=0.5,
            sample_size_control=50,
            sample_size_treatment=50,
            p_value=0.05,
        ),
        ABTestSummary(
            source_url="http://c.com",
            sample_size_control=10,
            sample_size_treatment=10,
            p_value=0.2,
        ),
    ]

    results = detect_outcome_types_for_batch(summaries)

    assert len(results) == 3
    assert results[0][1] == OUTCOME_TYPE_BINARY
    assert results[1][1] == OUTCOME_TYPE_CONTINUOUS
    assert results[2][1] == OUTCOME_TYPE_UNKNOWN