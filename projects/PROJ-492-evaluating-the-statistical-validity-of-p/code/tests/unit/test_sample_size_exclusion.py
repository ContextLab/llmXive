"""
Test for T025c: Verify that summaries flagged for sample-size mismatch
are not included in output/prevalence.json.

This test validates FR-004b compliance.
"""

import pytest
from pathlib import Path
import json
import tempfile
from datetime import datetime

from code.src.audit.validator import (
    validate_summary,
    filter_for_prevalence,
    write_audit_report
)
from code.src.models.data_models import ABTestSummary, AuditRecord


def test_sample_size_mismatch_excluded_from_prevalence():
    """
    Test that records with sample-size mismatches are excluded
    when filtering for prevalence estimates.
    """
    # Create a summary with sample-size mismatch
    summary_mismatch = ABTestSummary(
        url="https://example.com/test1",
        domain="example.com",
        sample_size_control=None,  # Missing control size
        sample_size_treatment=1000,
        p_value_reported=0.05,
        p_value_reconstructed=0.051,
        effect_size_reported=0.05,
        effect_size_reconstructed=0.05
    )

    # Create a valid summary
    summary_valid = ABTestSummary(
        url="https://example.com/test2",
        domain="example.com",
        sample_size_control=1000,
        sample_size_treatment=1000,
        p_value_reported=0.05,
        p_value_reconstructed=0.051,
        effect_size_reported=0.05,
        effect_size_reconstructed=0.05
    )

    # Validate both summaries
    record_mismatch = validate_summary(summary_mismatch)
    record_valid = validate_summary(summary_valid)

    # Verify that the mismatch record has a data_quality_warning
    assert record_mismatch.data_quality_warning is not None
    assert "Sample size mismatch" in record_mismatch.data_quality_warning

    # Verify that the valid record has no warning
    assert record_valid.data_quality_warning is None

    # Filter for prevalence
    all_records = [record_mismatch, record_valid]
    filtered_records = filter_for_prevalence(all_records)

    # Verify that the mismatch record is excluded
    assert record_mismatch not in filtered_records
    assert record_valid in filtered_records

    # Verify that only the valid record remains
    assert len(filtered_records) == 1
    assert filtered_records[0].url == "https://example.com/test2"


def test_filter_preserves_other_warnings():
    """
    Test that records with other types of warnings (not sample-size)
    are still included in prevalence estimates.
    """
    # Create a record with a non-sample-size warning
    record_other_warning = AuditRecord(
        url="https://example.com/test1",
        domain="example.com",
        data_quality_warning="Some other data quality issue"
    )

    # Create a record with sample-size warning
    record_sample_size_warning = AuditRecord(
        url="https://example.com/test2",
        domain="example.com",
        data_quality_warning="Sample size mismatch detected: Missing sample_size_control"
    )

    # Create a valid record
    record_valid = AuditRecord(
        url="https://example.com/test3",
        domain="example.com",
        data_quality_warning=None
    )

    all_records = [record_other_warning, record_sample_size_warning, record_valid]
    filtered_records = filter_for_prevalence(all_records)

    # Only sample-size mismatches should be excluded
    assert record_sample_size_warning not in filtered_records
    assert record_other_warning in filtered_records
    assert record_valid in filtered_records
    assert len(filtered_records) == 2
