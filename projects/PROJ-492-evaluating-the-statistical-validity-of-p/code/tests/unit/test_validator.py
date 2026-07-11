"""
Unit tests for the inconsistency validator (T025).
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime
import pytest
import numpy as np

from code.src.models.data_models import ABTestSummary
from code.src.audit.validator import (
    validate_single_summary,
    validate_all_summaries,
    run_validator,
    ABSOLUTE_P_DIFFERENCE_THRESHOLD,
    RELATIVE_EFFECT_SIZE_THRESHOLD
)
from code.src.utils.logger import get_default_logger


@pytest.fixture
def valid_summary():
    return ABTestSummary(
        url="http://example.com/test1",
        domain="example.com",
        publication_year=2023,
        sample_size_control=1000,
        sample_size_treatment=1000,
        conversion_rate_control=0.10,
        conversion_rate_treatment=0.12,
        p_value=0.03,
        effect_size=0.02,
        source_file="test.html"
    )


@pytest.fixture
def mismatched_summary():
    # Summary with conflicting sample sizes or invalid data
    return ABTestSummary(
        url="http://example.com/test2",
        domain="example.com",
        publication_year=2023,
        sample_size_control=0, # Invalid
        sample_size_treatment=1000,
        conversion_rate_control=0.10,
        conversion_rate_treatment=0.12,
        p_value=0.03,
        effect_size=0.02,
        source_file="test.html"
    )


def test_validate_consistent_summary(valid_summary):
    """Test that a consistent summary passes validation."""
    reconstructed_p = 0.031
    reconstructed_eff = 0.021
    logger = get_default_logger()

    record = validate_single_summary(valid_summary, reconstructed_p, reconstructed_eff, logger)

    assert not record.is_inconsistent
    assert len(record.inconsistencies) == 0
    assert len(record.data_quality_warnings) == 0


def test_validate_p_value_mismatch(valid_summary):
    """Test detection of p-value difference > 0.05."""
    reconstructed_p = 0.10 # Difference = 0.07 > 0.05
    reconstructed_eff = 0.02
    logger = get_default_logger()

    record = validate_single_summary(valid_summary, reconstructed_p, reconstructed_eff, logger)

    assert record.is_inconsistent
    assert len(record.inconsistencies) == 1
    assert record.inconsistencies[0]["type"] == "p_value_mismatch"
    assert record.inconsistencies[0]["difference"] > ABSOLUTE_P_DIFFERENCE_THRESHOLD


def test_validate_effect_size_mismatch(valid_summary):
    """Test detection of relative effect size difference > 5%."""
    # Reported: 0.02. 5% of 0.02 is 0.001.
    # If reconstructed is 0.025, diff is 0.005. Rel diff = 0.005 / 0.02 = 0.25 (25%) > 5%
    reconstructed_p = 0.03
    reconstructed_eff = 0.025
    logger = get_default_logger()

    record = validate_single_summary(valid_summary, reconstructed_p, reconstructed_eff, logger)

    assert record.is_inconsistent
    assert len(record.inconsistencies) == 1
    assert record.inconsistencies[0]["type"] == "effect_size_mismatch"
    assert record.inconsistencies[0]["relative_difference"] > RELATIVE_EFFECT_SIZE_THRESHOLD


def test_validate_sample_size_mismatch(mismatched_summary):
    """Test detection of sample size mismatch (invalid sample size)."""
    reconstructed_p = 0.03
    reconstructed_eff = None # Should be None due to invalid sample size
    logger = get_default_logger()

    record = validate_single_summary(mismatched_summary, reconstructed_p, reconstructed_eff, logger)

    assert record.is_inconsistent
    assert len(record.data_quality_warnings) > 0
    assert any("Sample size" in w for w in record.data_quality_warnings)


def test_validate_all_summaries():
    """Test validation of multiple summaries and JSON output."""
    summaries = [
        ABTestSummary(
            url="http://a.com", domain="a.com", publication_year=2023,
            sample_size_control=100, sample_size_treatment=100,
            conversion_rate_control=0.1, conversion_rate_treatment=0.11,
            p_value=0.04, effect_size=0.01, source_file="a.html"
        ),
        ABTestSummary(
            url="http://b.com", domain="b.com", publication_year=2023,
            sample_size_control=100, sample_size_treatment=100,
            conversion_rate_control=0.1, conversion_rate_treatment=0.20,
            p_value=0.01, effect_size=0.10, source_file="b.html"
        )
    ]

    reconstructed_results = {
        "http://a.com": {"p_value": 0.041, "effect_size": 0.011}, # Consistent
        "http://b.com": {"p_value": 0.10, "effect_size": 0.10} # P-value mismatch (0.09 diff)
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "audit_report.json"
        records = validate_all_summaries(summaries, reconstructed_results, output_path)

        assert len(records) == 2
        assert not records[0].is_inconsistent
        assert records[1].is_inconsistent

        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[1]["is_inconsistent"] is True
