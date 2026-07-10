"""
Unit tests for the inconsistency validator.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from code.src.models.data_models import ABTestSummary, AuditRecord
from code.src.audit.validator import (
    validate_single_summary,
    validate_all_summaries,
    filter_for_prevalence,
    write_audit_report,
    P_VALUE_THRESHOLD,
    EFFECT_SIZE_RELATIVE_THRESHOLD
)


@pytest.fixture
def sample_summary():
    return ABTestSummary(
        url="https://example.com/test1",
        domain="example.com",
        p_value=0.03,
        effect_size=0.15,
        sample_size_control=500,
        sample_size_treatment=500,
        baseline_conversion_rate=0.10
    )


@pytest.fixture
def sample_reconstruction():
    return {
        'sample_size_control': 500,
        'sample_size_treatment': 500,
        'reconstructed_p_value': 0.03,
        'reconstructed_effect_size': 0.15
    }


def test_validate_consistent_summary(sample_summary, sample_reconstruction):
    """Test that a consistent summary passes validation."""
    is_consistent, flag_reason, warning = validate_single_summary(
        sample_summary, sample_reconstruction
    )
    assert is_consistent is True
    assert flag_reason == "Consistent"
    assert warning is None


def test_validate_p_value_discrepancy(sample_summary):
    """Test detection of p-value discrepancy > 0.05."""
    reconstruction = sample_summary.__dict__.copy()
    reconstruction['reconstructed_p_value'] = 0.10  # Difference of 0.07

    is_consistent, flag_reason, warning = validate_single_summary(
        sample_summary, reconstruction
    )
    assert is_consistent is False
    assert "P-value discrepancy" in flag_reason
    assert warning is None


def test_validate_effect_size_discrepancy(sample_summary):
    """Test detection of effect size discrepancy > 5%."""
    reconstruction = sample_summary.__dict__.copy()
    # 10% relative difference (0.15 vs 0.135)
    reconstruction['reconstructed_effect_size'] = 0.135

    is_consistent, flag_reason, warning = validate_single_summary(
        sample_summary, reconstruction
    )
    assert is_consistent is False
    assert "Effect size discrepancy" in flag_reason
    assert warning is None


def test_validate_sample_size_mismatch(sample_summary):
    """Test detection of sample size mismatch."""
    reconstruction = sample_summary.__dict__.copy()
    reconstruction['reconstructed_p_value'] = 0.03
    reconstruction['reconstructed_effect_size'] = 0.15
    reconstruction['sample_size_control'] = 600  # Mismatch
    reconstruction['sample_size_treatment'] = 500

    is_consistent, flag_reason, warning = validate_single_summary(
        sample_summary, reconstruction
    )
    assert warning is not None
    assert "Sample size mismatch" in warning


def test_validate_all_summaries():
    """Test validation of multiple summaries."""
    summaries = [
        ABTestSummary(
            url=f"https://example.com/test{i}",
            domain="example.com",
            p_value=0.03,
            effect_size=0.15,
            sample_size_control=500,
            sample_size_treatment=500,
            baseline_conversion_rate=0.10
        )
        for i in range(3)
    ]

    reconstructions = [
        {'sample_size_control': 500, 'sample_size_treatment': 500, 'reconstructed_p_value': 0.03, 'reconstructed_effect_size': 0.15},
        {'sample_size_control': 500, 'sample_size_treatment': 500, 'reconstructed_p_value': 0.10, 'reconstructed_effect_size': 0.15},  # P-value mismatch
        {'sample_size_control': 600, 'sample_size_treatment': 500, 'reconstructed_p_value': 0.03, 'reconstructed_effect_size': 0.15},  # Sample size mismatch
    ]

    records = validate_all_summaries(summaries, reconstructions)

    assert len(records) == 3
    assert records[0].is_consistent is True
    assert records[1].is_consistent is False
    assert records[1].inconsistency_reason is not None
    assert records[2].has_sample_size_mismatch is True


def test_filter_for_prevalence():
    """Test that sample size mismatch records are filtered out."""
    records = [
        AuditRecord(
            url="https://example.com/1",
            domain="example.com",
            is_consistent=True,
            has_sample_size_mismatch=False,
            timestamp="2024-01-01T00:00:00"
        ),
        AuditRecord(
            url="https://example.com/2",
            domain="example.com",
            is_consistent=True,
            has_sample_size_mismatch=True,
            timestamp="2024-01-01T00:00:00"
        ),
        AuditRecord(
            url="https://example.com/3",
            domain="example.com",
            is_consistent=False,
            has_sample_size_mismatch=False,
            timestamp="2024-01-01T00:00:00"
        ),
    ]

    filtered = filter_for_prevalence(records)

    assert len(filtered) == 2
    assert filtered[0].url == "https://example.com/1"
    assert filtered[1].url == "https://example.com/3"
    assert all(not r.has_sample_size_mismatch for r in filtered)


def test_write_audit_report():
    """Test writing audit report to JSON."""
    records = [
        AuditRecord(
            url="https://example.com/1",
            domain="example.com",
            is_consistent=True,
            has_sample_size_mismatch=False,
            timestamp="2024-01-01T00:00:00"
        ),
        AuditRecord(
            url="https://example.com/2",
            domain="example.com",
            is_consistent=False,
            inconsistency_reason="Test reason",
            has_sample_size_mismatch=True,
            data_quality_warning="Sample size mismatch",
            timestamp="2024-01-01T00:00:00"
        ),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "audit_report.json"
        write_audit_report(records, output_path)

        assert output_path.exists()

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[0]['is_consistent'] is True
        assert data[1]['is_consistent'] is False
        assert data[1]['inconsistency_reason'] == "Test reason"
        assert data[1]['has_sample_size_mismatch'] is True
        assert data[1]['data_quality_warning'] == "Sample size mismatch"


def test_validate_all_summaries_mismatched_lengths():
    """Test that mismatched lengths raise an error."""
    summaries = [
        ABTestSummary(
            url="https://example.com/1",
            domain="example.com",
            p_value=0.03,
            effect_size=0.15,
            sample_size_control=500,
            sample_size_treatment=500,
            baseline_conversion_rate=0.10
        )
    ]
    reconstructions = [
        {'sample_size_control': 500, 'sample_size_treatment': 500, 'reconstructed_p_value': 0.03, 'reconstructed_effect_size': 0.15},
        {'sample_size_control': 500, 'sample_size_treatment': 500, 'reconstructed_p_value': 0.03, 'reconstructed_effect_size': 0.15},
    ]

    with pytest.raises(ValueError) as exc_info:
        validate_all_summaries(summaries, reconstructions)

    assert "does not match" in str(exc_info.value)
