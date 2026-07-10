"""
Unit test to verify that summaries flagged for sample-size mismatch
are not included in prevalence calculations.
"""

import json
import tempfile
from pathlib import Path

import pytest

from code.src.models.data_models import AuditRecord
from code.src.audit.validator import filter_for_prevalence, write_audit_report


@pytest.fixture
def sample_audit_records():
    """Create sample audit records with mixed sample size mismatch flags."""
    return [
        AuditRecord(
            url="https://example.com/consistent",
            domain="example.com",
            is_consistent=True,
            inconsistency_reason=None,
            data_quality_warning=None,
            has_sample_size_mismatch=False,
            timestamp="2024-01-01T00:00:00"
        ),
        AuditRecord(
            url="https://example.com/mismatch",
            domain="example.com",
            is_consistent=True,
            inconsistency_reason=None,
            data_quality_warning="Sample size mismatch detected",
            has_sample_size_mismatch=True,
            timestamp="2024-01-01T00:00:00"
        ),
        AuditRecord(
            url="https://example.com/inconsistent",
            domain="example.com",
            is_consistent=False,
            inconsistency_reason="P-value discrepancy",
            data_quality_warning=None,
            has_sample_size_mismatch=False,
            timestamp="2024-01-01T00:00:00"
        ),
        AuditRecord(
            url="https://example.com/mismatch_inconsistent",
            domain="example.com",
            is_consistent=False,
            inconsistency_reason="Effect size discrepancy",
            data_quality_warning="Sample size mismatch detected",
            has_sample_size_mismatch=True,
            timestamp="2024-01-01T00:00:00"
        ),
    ]


def test_filter_excludes_sample_size_mismatch(sample_audit_records):
    """Verify that records with sample_size_mismatch=True are excluded."""
    filtered = filter_for_prevalence(sample_audit_records)

    # Should only have 2 records (consistent and inconsistent without mismatch)
    assert len(filtered) == 2

    # Verify the URLs
    urls = [r.url for r in filtered]
    assert "https://example.com/consistent" in urls
    assert "https://example.com/inconsistent" in urls
    assert "https://example.com/mismatch" not in urls
    assert "https://example.com/mismatch_inconsistent" not in urls

    # Verify no record in filtered has has_sample_size_mismatch=True
    assert all(not r.has_sample_size_mismatch for r in filtered)


def test_filter_preserves_all_valid_records(sample_audit_records):
    """Verify that records without mismatch are preserved."""
    filtered = filter_for_prevalence(sample_audit_records)

    # Check that consistent records are preserved
    consistent_records = [r for r in filtered if r.is_consistent]
    assert len(consistent_records) == 1
    assert consistent_records[0].url == "https://example.com/consistent"

    # Check that inconsistent records (without mismatch) are preserved
    inconsistent_records = [r for r in filtered if not r.is_consistent]
    assert len(inconsistent_records) == 1
    assert inconsistent_records[0].url == "https://example.com/inconsistent"


def test_filter_with_all_mismatches():
    """Test filtering when all records have sample size mismatch."""
    all_mismatch_records = [
        AuditRecord(
            url=f"https://example.com/{i}",
            domain="example.com",
            is_consistent=True,
            has_sample_size_mismatch=True,
            timestamp="2024-01-01T00:00:00"
        )
        for i in range(3)
    ]

    filtered = filter_for_prevalence(all_mismatch_records)
    assert len(filtered) == 0


def test_filter_with_no_mismatches():
    """Test filtering when no records have sample size mismatch."""
    no_mismatch_records = [
        AuditRecord(
            url=f"https://example.com/{i}",
            domain="example.com",
            is_consistent=(i % 2 == 0),
            has_sample_size_mismatch=False,
            timestamp="2024-01-01T00:00:00"
        )
        for i in range(3)
    ]

    filtered = filter_for_prevalence(no_mismatch_records)
    assert len(filtered) == 3
    assert all(not r.has_sample_size_mismatch for r in filtered)
